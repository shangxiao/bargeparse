import os
import sys

import pytest

if sys.version_info <= (3, 8):
    collect_ignore = ["test_positional_only_parameters.py"]


class ExitException(Exception):
    ...


def raise_an_exception(_):
    raise ExitException()


@pytest.fixture
def prepare_for_output(monkeypatch):
    # terminal size affects output display so force a consistent size
    monkeypatch.setattr(
        "shutil.get_terminal_size",
        lambda *args, **kwargs: os.terminal_size((1000, 1000)),
    )
    # raise an exception instead of exiting (or attempting to call func() with missing args)
    monkeypatch.setattr("argparse._sys.exit", raise_an_exception)
