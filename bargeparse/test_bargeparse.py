from bargeparse.command import command


def test_args_and_kwargs(monkeypatch):
    captured_a = None
    captured_b = None
    captured_c = None
    captured_d = None
    monkeypatch.setattr(
        "argparse._sys.argv", ["", "--c", "fizz", "--d", "buzz", "foo", "bar"]
    )

    def func(a, b, c=None, d=None):
        nonlocal captured_a
        nonlocal captured_b
        nonlocal captured_c
        nonlocal captured_d
        captured_a = a
        captured_b = b
        captured_c = c
        captured_d = d

    command(func)()

    assert captured_a == "foo"
    assert captured_b == "bar"
    assert captured_c == "fizz"
    assert captured_d == "buzz"


def test_pos_only_args(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "foo"])

    def func(a, /):
        nonlocal captured_a
        captured_a = a

    command(func)()

    assert captured_a == "foo"


def test_keyword_only_args(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--a", "foo"])

    def func(*, a):
        nonlocal captured_a
        captured_a = a

    command(func)()

    assert captured_a == "foo"


def test_docstring(monkeypatch, capsys):
    monkeypatch.setattr("argparse._sys.argv", ["", "--help"])
    monkeypatch.setattr("argparse._sys.exit", lambda _: _)

    def func():
        """
        Helpful help message
        """

    command(func)()

    assert (
        capsys.readouterr().out
        == """\
usage: [-h]

Helpful help message

optional arguments:
  -h, --help  show this help message and exit
"""
    )


def test_typehint(monkeypatch):
    monkeypatch.setattr("argparse._sys.argv", ["", "1"])
    captured_a = None

    def func(a: int):
        nonlocal captured_a
        captured_a = a

    command(func)()

    assert captured_a == 1
