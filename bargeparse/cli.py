import argparse
import datetime
import inspect

import dateutil.parser

from . import actions


def date_parser_type(date_str):
    return dateutil.parser.parse(date_str).date()


def is_positional(param):
    return (
        param.kind == inspect.Parameter.POSITIONAL_ONLY
        or param.default == inspect.Parameter.empty
        and param.kind != inspect.Parameter.KEYWORD_ONLY
    )


def get_param_type(param):
    if param.annotation == datetime.date:
        return date_parser_type
    elif param.annotation == datetime.datetime:
        return dateutil.parser.parse
    return param.annotation if param.annotation != inspect.Parameter.empty else None


def cli(func):
    parser = argparse.ArgumentParser(description=func.__doc__)
    params = inspect.signature(func).parameters.values()
    for param in params:
        param_type = get_param_type(param)

        if param_type == bool:
            # booleans are a special case for both positional & keyword arguments
            parser.add_argument(
                f"--{param.name}",
                action=(
                    actions.BooleanOptionalAction
                    if is_positional(param)
                    else f"store_{str(not param.default).lower()}"
                ),
            )
        else:
            if is_positional(param):
                parser.add_argument(
                    param.name,
                    type=param_type,
                )
            else:
                parser.add_argument(
                    f"--{param.name}",
                    default=param.default,
                    required=param.kind == inspect.Parameter.KEYWORD_ONLY,
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
