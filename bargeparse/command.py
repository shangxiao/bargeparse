import functools

from bargeparse.cli import cli


def command(*args, param_factories=None):
    def decorator(func):
        func._subcommands = []
        func.subcommand = functools.partial(
            subcommand, func, param_factories=param_factories
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If there are args or kwargs, then assume that func() is being called
            # directly and is not from the command line.
            if len(args) > 0 or len(kwargs) > 0:
                return func(*args, **kwargs)
            cli(func, param_factories=param_factories)

        return wrapper

    if len(args) > 0 and callable(args[0]):
        return decorator(args[0])
    else:
        return decorator


def subcommand(parent_command, *args, param_factories=None):
    def decorator(func):
        parent_command._subcommands.append(func)
        return func

    if len(args) > 0 and callable(args[0]):
        return decorator(args[0])
    else:
        return decorator
