import os

import pytest

from bargeparse import command


def test_pos_only_args(monkeypatch):
    captured_a = None
    captured_b = None
    captured_c = None
    monkeypatch.setattr("argparse._sys.argv", ["", "foo", "bar"])

    @command
    def func(a, b="b", c="c", /):
        nonlocal captured_a
        nonlocal captured_b
        nonlocal captured_c
        captured_a = a
        captured_b = b
        captured_c = c

    func()

    assert captured_a == "foo"
    assert captured_b == "bar"
    assert captured_c == "c"


def test_help_renders_docstring_and_correct_help_messages(monkeypatch, capsys):
    def raise_an_exception(_):
        raise Exception()

    monkeypatch.setattr("argparse._sys.argv", ["", "--help"])
    # raise an exception instead of exiting (or attempting to call func() with missing args)
    monkeypatch.setattr("argparse._sys.exit", raise_an_exception)
    monkeypatch.setattr(
        "shutil.get_terminal_size", lambda: os.terminal_size((1000, 1000))
    )

    @command
    def func(
        arg_1,
        arg_2: bool,
        arg_3: bool = False,
        arg_4=None,
        arg_5="arg_5",
        /,
        *,
        kwarg_1,
        kwarg_2: bool,
        kwarg_3="kwarg_3",
        kwarg_4=None,
        kwarg_5: bool = False,
    ):
        """
        Helpful help message.

        This paragraph should describe the command in more detail.
        """

    with pytest.raises(Exception):
        func()

    assert (
        capsys.readouterr().out
        == """\
usage: [-h] --arg-2 [--arg-3] --kwarg-1 KWARG_1 --kwarg-2 [--kwarg-3 KWARG_3] [--kwarg-4 KWARG_4] [--kwarg-5] arg-1 [arg-4] [arg-5]

Helpful help message.

This paragraph should describe the command in more detail.

positional arguments:
  arg-1
  arg-4
  arg-5                 default: arg_5

optional arguments:
  -h, --help            show this help message and exit
  --arg-2, --no-arg-2   required
  --arg-3
  --kwarg-1 KWARG_1     required
  --kwarg-2, --no-kwarg-2
                        required
  --kwarg-3 KWARG_3     default: kwarg_3
  --kwarg-4 KWARG_4
  --kwarg-5
"""
    )
