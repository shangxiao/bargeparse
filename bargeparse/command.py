import functools

from bargeparse.cli import cli


def command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) > 0 or len(kwargs) > 0:
            return func(*args, **kwargs)
        cli(func)

    return wrapper
