import argparse
import ast
import datetime
import enum
import inspect
import io
import itertools
import re
import textwrap
import token
import tokenize
import typing

from . import actions

LIST_TYPES = (
    typing.List,
    typing.Tuple,
    # as of Python 3.9
    list,
    tuple,
)

TOKENS_PRECEDING_PARAM = (
    token.LPAR,
    token.COMMA,
    tokenize.NL,  # only in tokenize <3.7
)


def kebab_case(string):
    return string.strip("_").replace("_", "-")


def is_positional(param):
    return (
        param.kind == inspect.Parameter.POSITIONAL_ONLY
        or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        and param.default == inspect.Parameter.empty
    )


def date_parser(date_str):
    return datetime.datetime.strptime(re.sub(r"\D", " ", date_str), "%Y %m %d").date()


def datetime_parser(date_str):
    return datetime.datetime.strptime(re.sub(r"\D", " ", date_str), "%Y %m %d %H %M %S")


def get_param_factory(param, param_factories=None):
    if param.annotation == inspect.Parameter.empty:
        return None
    elif param.annotation == datetime.date:
        return date_parser
    elif param.annotation == datetime.datetime:
        return datetime_parser
    elif param_factories is not None and param.annotation in param_factories:
        return param_factories[param.annotation]
    else:
        return param.annotation


def define_params(params, parser, param_factories, param_comments):
    for param in params:
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        param_display_name = kebab_case(param.name)
        has_default = param.default != inspect.Parameter.empty

        help_msg = param_comments.get(param.name)
        additional_help_parts = {
            "required": (
                not has_default
                and (not is_positional(param) or param.annotation == bool)
            ),
            f"default: {param.default}": (
                has_default and param.default is not None and param.annotation != bool
            ),
        }
        additional_help_msg = ", ".join(
            part for part, pred in additional_help_parts.items() if pred
        )
        if help_msg and additional_help_msg:
            help_msg = f"{help_msg} ({additional_help_msg})"
        elif additional_help_msg:
            help_msg = f"({additional_help_msg})"

        if param.annotation == bool:
            # booleans are always optional for both types of parameters
            arg_name = f"--{param_display_name}"
            arg_options = dict(
                dest=param.name,
                action=(
                    actions.BooleanOptionalAction
                    if not has_default
                    else f"store_{str(not param.default).lower()}"
                ),
                required=not has_default,
                help=help_msg,
            )
        else:
            arg_type = get_param_factory(param, param_factories)
            nargs = None
            action = None

            # support for list, list[...], tuple or tuple[...] types
            list_type = (
                getattr(param.annotation, "__origin__", param.annotation)
                # Note: in Python 3.6 typing.List.__origin__ would return None
                or param.annotation
            )
            if list_type in LIST_TYPES:
                nargs = "*"
                # be sure to replace the list type with something meaningful if specified, otherwise nothing
                has_type = (
                    hasattr(param.annotation, "__args__")
                    # __args__ is None in Python 3.6
                    and param.annotation.__args__
                    # typing.List seems to have a T type var even if not specified on 3.8.5 ?
                    and type(param.annotation.__args__[0]) != typing.TypeVar
                )
                if has_type:
                    arg_type = param.annotation.__args__[0]
                else:
                    arg_type = None
                if list_type in (tuple, typing.Tuple):
                    action = actions.TupleAction

            # support for enums
            # requires a special action due to enums not being properly supported,
            # see: https://bugs.python.org/issue42501
            if inspect.isclass(arg_type) and issubclass(arg_type, enum.Enum):
                action = actions.enum_action_factory(
                    arg_type, use_tuple=action == actions.TupleAction
                )
                arg_type = None

            if is_positional(param):
                arg_name = param.name
                arg_options = dict(
                    metavar=param_display_name,
                    default=argparse.SUPPRESS,
                    # nargs="?" can make a posarg "optional"
                    nargs="?" if has_default else nargs,
                    type=arg_type,
                    action=action,
                    help=help_msg,
                )
            else:
                arg_name = f"--{param_display_name}"
                arg_options = dict(
                    dest=param.name,
                    default=argparse.SUPPRESS,
                    required=not has_default,
                    nargs=nargs,
                    type=arg_type,
                    action=action,
                    help=help_msg,
                )

        parser.add_argument(arg_name, **arg_options)


def get_param_comments(func):
    params = inspect.signature(func).parameters
    source = inspect.getsource(func)
    body_lineno = ast.parse(textwrap.dedent(source)).body[0].body[0].lineno
    tokens = tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline)
    prev_t = None
    prev_name = None
    prev_name_line = None
    comments = {}
    for t in tokens:
        if t.start[0] >= body_lineno:
            break
        if (
            t.exact_type == token.NAME
            and t.string in params
            and prev_t.exact_type in TOKENS_PRECEDING_PARAM
        ):
            prev_name = t.string
            prev_name_line = t.start[0]
        # <3.7 COMMENT is only available in tokenize
        if (
            t.exact_type == tokenize.COMMENT
            and prev_name
            # only comments on the same line as the param are accepted
            and prev_name_line == t.start[0]
        ):
            comments[prev_name] = t.string.lstrip("#").strip()
        prev_t = t
    return comments


def cli(func, param_factories=None):
    description = textwrap.dedent(func.__doc__).strip() if func.__doc__ else None
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    params = inspect.signature(func).parameters.values()

    if "parser" in (p.name for p in params):
        inner_func = func(parser)
        params = inspect.signature(inner_func).parameters.values()
        param_comments = get_param_comments(inner_func)
        parser.set_defaults(target_func=inner_func)
    else:
        param_comments = get_param_comments(func)
        parser.set_defaults(target_func=func)

    define_params(params, parser, param_factories, param_comments)

    if func._subcommands:
        subparsers = parser.add_subparsers()
        for subcommand in func._subcommands:
            subcommand_description = (
                textwrap.dedent(subcommand.__doc__).strip()
                if subcommand.__doc__
                else None
            )
            subcommand_summary = (
                " ".join(
                    itertools.takewhile(
                        lambda line: line.strip(), subcommand_description.splitlines()
                    )
                )
                if subcommand_description
                else None
            )
            subparser = subparsers.add_parser(
                kebab_case(subcommand.__name__),
                description=subcommand_description,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                help=subcommand_summary,
            )
            subparser.set_defaults(target_func=subcommand)
            subcommand_params = inspect.signature(subcommand).parameters.values()
            subcommand_param_comments = get_param_comments(subcommand)
            define_params(
                subcommand_params, subparser, param_factories, subcommand_param_comments
            )

    arg_namespace = parser.parse_args()

    if func._subcommands:
        all_params = list(
            itertools.chain(
                params, inspect.signature(arg_namespace.target_func).parameters.values()
            )
        )
    else:
        all_params = params

    args = []
    kwargs = {}

    # populate the args & kwargs to pass to the target function
    for param in all_params:
        if param.name not in arg_namespace:
            # skip suppressed optional args with defaults that were not supplied
            # as well as any variable args
            continue
        if is_positional(param):
            args.append(getattr(arg_namespace, param.name))
        else:
            kwargs[param.name] = getattr(arg_namespace, param.name)

    # add remaining arguments added from custom parser arguments
    remaining_arguments = {
        k: getattr(arg_namespace, k)
        for k in vars(arg_namespace).keys()
        if k not in (p.name for p in all_params) and k != "target_func"
    }
    kwargs = {**kwargs, **remaining_arguments}

    # pass the parser if variable keyword parameter present
    if inspect.Parameter.VAR_KEYWORD in (
        p.kind
        for p in inspect.signature(
            getattr(arg_namespace, "target_func")
        ).parameters.values()
    ):
        kwargs["parser"] = parser

    getattr(arg_namespace, "target_func")(*args, **kwargs)
