import functools

from bargeparse.cli import cli


def command(*args, param_factories=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 0 or len(kwargs) > 0:
                return func(*args, **kwargs)
            cli(func, param_factories=param_factories)

        return wrapper

    if len(args) > 0 and callable(args[0]):
        return decorator(args[0])
    else:
        return decorator
