from datetime import date, datetime

import pytest

from bargeparse.command import command


def test_args_and_kwargs(monkeypatch):
    captured_a = None
    captured_b = None
    captured_c = None
    captured_d = None
    monkeypatch.setattr(
        "argparse._sys.argv", ["", "--c", "fizz", "--d", "buzz", "foo", "bar"]
    )

    @command
    def func(a, b, c=None, d=None):
        nonlocal captured_a
        nonlocal captured_b
        nonlocal captured_c
        nonlocal captured_d
        captured_a = a
        captured_b = b
        captured_c = c
        captured_d = d

    func()

    assert captured_a == "foo"
    assert captured_b == "bar"
    assert captured_c == "fizz"
    assert captured_d == "buzz"


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


def test_keyword_only_args(monkeypatch):
    captured_a = None
    captured_b = None
    captured_c = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--a", "foo", "--b", "bar"])

    @command
    def func(*, a, b="b", c="c"):
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


def test_converts_arg_names_to_kebab_case(monkeypatch):
    captured_positional_argument = None
    captured_optional_argument = None
    monkeypatch.setattr("argparse._sys.argv", ["", "foo", "--optional-argument", "bar"])

    @command
    def func(positional_argument, optional_argument="buzz"):
        nonlocal captured_positional_argument
        nonlocal captured_optional_argument
        captured_positional_argument = positional_argument
        captured_optional_argument = optional_argument

    func()

    assert captured_positional_argument == "foo"
    assert captured_optional_argument == "bar"


def test_docstring(monkeypatch, capsys):
    monkeypatch.setattr("argparse._sys.argv", ["", "--help"])
    monkeypatch.setattr("argparse._sys.exit", lambda _: _)

    @command
    def func():
        """
        Helpful help message
        """

    func()

    assert (
        capsys.readouterr().out
        == """\
usage: [-h]

Helpful help message

optional arguments:
  -h, --help  show this help message and exit
"""
    )


@pytest.mark.parametrize(
    "input_type,input,expected",
    (
        (str, "1", "1"),
        (int, "1", 1),
        (float, "0.25", 0.25),
        (bool, "--a", True),
        (bool, "--no-a", False),
        (date, "2000-01-01", date(2000, 1, 1)),
        (datetime, "2000-01-01 12:15:30", datetime(2000, 1, 1, 12, 15, 30)),
    ),
)
def test_typehint(monkeypatch, input_type, input, expected):
    monkeypatch.setattr("argparse._sys.argv", ["", input])
    captured_a = None

    @command
    def func(a: input_type):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == expected


@pytest.mark.parametrize(
    "param_default,input,expected",
    (
        (False, "--a", True),
        (False, None, False),
        (True, "--a", False),
        (True, None, True),
    ),
)
def test_typehint_optional_boolean(monkeypatch, param_default, input, expected):
    if input:
        monkeypatch.setattr("argparse._sys.argv", ["", input])
    captured_a = None

    @command
    def func(a: bool = param_default):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == expected
