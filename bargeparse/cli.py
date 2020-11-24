import argparse
import datetime
import enum
import inspect
import itertools
import re
import textwrap
import typing

from . import actions

LIST_TYPES = (
    typing.List,
    list,  # as of Python 3.9
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


def define_params(params, parser, param_factories):
    for param in params:
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        param_display_name = kebab_case(param.name)
        has_default = param.default != inspect.Parameter.empty
        help_parts = {
            "required": (
                not has_default
                and (not is_positional(param) or param.annotation == bool)
            ),
            f"default: {param.default}": (
                has_default and param.default is not None and param.annotation != bool
            ),
        }
        help_msg = ", ".join(part for part, pred in help_parts.items() if pred)

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

            # support for list or list[...] types
            if (
                getattr(param.annotation, "__origin__", param.annotation)
                # Note: in Python 3.6 typing.List.__origin__ would return None
                or param.annotation
            ) in LIST_TYPES:
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

            # support for enums
            # requires a special action due to enums not being properly supported,
            # see: https://bugs.python.org/issue42501
            if inspect.isclass(arg_type) and issubclass(arg_type, enum.Enum):
                action = actions.enum_action_factory(arg_type)
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


def cli(func, param_factories=None):
    description = textwrap.dedent(func.__doc__) if func.__doc__ else None
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    params = inspect.signature(func).parameters.values()
    define_params(params, parser, param_factories)

    if func._subcommands:
        subparsers = parser.add_subparsers()
        for subcommand in func._subcommands:
            subcommand_description = (
                textwrap.dedent(subcommand.__doc__) if subcommand.__doc__ else None
            )
            subparser = subparsers.add_parser(
                kebab_case(subcommand.__name__),
                description=subcommand_description,
                help=subcommand_description,
            )
            subparser.set_defaults(func=subcommand)
            subcommand_params = inspect.signature(subcommand).parameters.values()
            define_params(subcommand_params, subparser, param_factories)

    arg_namespace = parser.parse_args()

    if func._subcommands and hasattr(arg_namespace, "func"):
        all_params = itertools.chain(
            params, inspect.signature(arg_namespace.func).parameters.values()
        )
    else:
        all_params = params

    args = []
    kwargs = {}
    for param in all_params:
        if param.name not in arg_namespace:
            # skip suppressed optional args with defaults that were not supplied
            continue
        if is_positional(param):
            args.append(getattr(arg_namespace, param.name))
        else:
            kwargs[param.name] = getattr(arg_namespace, param.name)

    getattr(arg_namespace, "func", func)(*args, **kwargs)
