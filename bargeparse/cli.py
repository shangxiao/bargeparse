import argparse
import datetime
import inspect
import re
import textwrap
import typing

from . import actions

LIST_TYPES = (
    typing.List,
    list,  # as of Python 3.9
)


def date_parser(date_str):
    return datetime.datetime.strptime(re.sub(r"\D", " ", date_str), "%Y %m %d").date()


def datetime_parser(date_str):
    return datetime.datetime.strptime(re.sub(r"\D", " ", date_str), "%Y %m %d %H %M %S")


def is_positional(param):
    return (
        param.kind == inspect.Parameter.POSITIONAL_ONLY
        or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        and param.default == inspect.Parameter.empty
    )


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


def cli(func, param_factories=None):
    description = textwrap.dedent(func.__doc__) if func.__doc__ else None
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    params = inspect.signature(func).parameters.values()
    for param in params:
        param_display_name = param.name.strip("_").replace("_", "-")
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
            param_factory = get_param_factory(param, param_factories)

            if is_positional(param):
                arg_name = param.name
                arg_options = dict(
                    metavar=param_display_name,
                    default=argparse.SUPPRESS,
                    # nargs="?" can make a posarg "optional"
                    nargs="?" if has_default else None,
                    type=param_factory,
                    help=help_msg,
                )
            else:
                arg_name = f"--{param_display_name}"
                arg_options = dict(
                    dest=param.name,
                    default=argparse.SUPPRESS,
                    required=not has_default,
                    type=param_factory,
                    help=help_msg,
                )

            # support for list or list[T] types
            if (
                getattr(param.annotation, "__origin__", param.annotation)
                # Note: in Python 3.6 typing.List.__origin__ would return None
                or param.annotation
            ) in LIST_TYPES:
                arg_options["nargs"] = "*"
                # be sure to replace the list type with something meaningful if specified, otherwise nothing
                arg_options["type"] = (
                    param.annotation.__args__[0]
                    if hasattr(param.annotation, "__args__")
                    # __args__ is None in Python 3.6
                    and param.annotation.__args__
                    # typing.List seems to have a T type var even if not specified on 3.8.5 ?
                    and type(param.annotation.__args__[0]) != typing.TypeVar
                    else None
                )

        parser.add_argument(arg_name, **arg_options)

    arg_namespace = parser.parse_args()
    args = []
    kwargs = {}
    for param in params:
        if param.name not in arg_namespace:
            # skip suppressed optional args with defaults that were not supplied
            continue
        if is_positional(param):
            args.append(getattr(arg_namespace, param.name))
        else:
            kwargs[param.name] = getattr(arg_namespace, param.name)
    func(*args, **kwargs)
