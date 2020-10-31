import argparse
import datetime
import inspect
import re

from . import actions


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


def get_param_factory(param):
    if param.annotation == inspect.Parameter.empty:
        return None
    elif param.annotation == datetime.date:
        return date_parser
    elif param.annotation == datetime.datetime:
        return datetime_parser
    else:
        return param.annotation


def cli(func):
    parser = argparse.ArgumentParser(description=func.__doc__)
    params = inspect.signature(func).parameters.values()
    for param in params:
        param_name = param.name.replace("_", "-")
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
            # booleans are always optional for both args & kwargs
            parser.add_argument(
                f"--{param_name}",
                action=(
                    actions.BooleanOptionalAction
                    if not has_default
                    else f"store_{str(not param.default).lower()}"
                ),
                required=not has_default,
                help=help_msg,
            )
        else:
            param_factory = get_param_factory(param)
            if is_positional(param):
                parser.add_argument(
                    param_name,
                    default=param.default if has_default else None,
                    # nargs="?" can make a posarg "optional"
                    nargs="?" if has_default else None,
                    type=param_factory,
                    help=help_msg,
                )
            else:
                parser.add_argument(
                    f"--{param_name}",
                    default=param.default if has_default else None,
                    required=not has_default,
                    type=param_factory,
                    help=help_msg,
                )

    arg_namespace = parser.parse_args()
    args = []
    kwargs = {}
    for param in params:
        # For some reason optional arguments get converted back to underscores in the Namespace object,
        # so just use the original param.name to reference the value.
        param_value = getattr(
            arg_namespace,
            param.name.replace("_", "-")
            if is_positional(param) and param.annotation != bool
            else param.name,
        )
        if is_positional(param):
            args.append(param_value)
        else:
            kwargs[param.name] = param_value
    func(*args, **kwargs)
