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
    monkeypatch.setattr("argparse._sys.argv", ["", "foo"])

    @command
    def func(a, /):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == "foo"


def test_keyword_only_args(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--a", "foo"])

    @command
    def func(*, a):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == "foo"


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
        (bool, "t", True),
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
