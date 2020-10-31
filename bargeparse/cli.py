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


def get_param_type(param):
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
        param_type = get_param_type(param)
        has_default = param.default != inspect.Parameter.empty

        if param_type == bool:
            # booleans are a special case for both positional & keyword arguments
            parser.add_argument(
                f"--{param.name}",
                action=(
                    actions.BooleanOptionalAction
                    if not has_default
                    else f"store_{str(not param.default).lower()}"
                ),
                required=not has_default,
            )
        else:
            if is_positional(param):
                parser.add_argument(
                    param.name,
                    default=param.default if has_default else None,
                    # nargs="?" can make a posarg "optional"
                    nargs="?" if has_default else None,
                    type=param_type,
                )
            else:
                parser.add_argument(
                    f"--{param.name}",
                    default=param.default if has_default else None,
                    required=not has_default,
                    type=param_type,
                )

    arg_namespace = parser.parse_args()
    args = []
    kwargs = {}
    for param in params:
        if is_positional(param):
            args.append(getattr(arg_namespace, param.name))
        else:
            kwargs[param.name] = getattr(arg_namespace, param.name)
    func(*args, **kwargs)
