import enum
import os
import pathlib
import sys
import typing
from dataclasses import dataclass
from datetime import date, datetime

import pytest

from bargeparse import command, subcommand


def test_command_no_params(monkeypatch):
    func_run = False
    monkeypatch.setattr("argparse._sys.argv", [""])

    @command
    def func():
        nonlocal func_run
        func_run = True

    func()

    assert func_run


def test_command_can_be_called_directly_bypassing_cli_parsing():
    captured_a = None

    @command
    def func(a):
        nonlocal captured_a
        captured_a = a

    func("foo")

    assert captured_a == "foo"


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
    captured_arg_surrounded_by_underscores = None
    monkeypatch.setattr(
        "argparse._sys.argv",
        [
            "",
            "foo",
            "--optional-argument",
            "bar",
            "--arg-surrounded-by-underscores",
            "buzz",
        ],
    )

    @command
    def func(
        positional_argument,
        optional_argument="buzz",
        __arg_surrounded_by_underscores___=None,
    ):
        nonlocal captured_positional_argument
        nonlocal captured_optional_argument
        nonlocal captured_arg_surrounded_by_underscores
        captured_positional_argument = positional_argument
        captured_optional_argument = optional_argument
        captured_arg_surrounded_by_underscores = __arg_surrounded_by_underscores___

    func()

    assert captured_positional_argument == "foo"
    assert captured_optional_argument == "bar"
    assert captured_arg_surrounded_by_underscores == "buzz"


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
        (pathlib.Path, ".", pathlib.Path(".")),
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
    params = [""]
    if input:
        params += [input]
    monkeypatch.setattr("argparse._sys.argv", params)
    captured_a = None

    @command
    def func(a: bool = param_default):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == expected


def test_custom_type_factory(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "foo"])

    @dataclass
    class CustomType:
        a: str

    @command
    def func(a: CustomType):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == CustomType("foo")


@pytest.mark.parametrize(
    "list_type,input_value,expected",
    (
        pytest.param(
            list,
            ["a", "b"],
            ["a", "b"],
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Builtin type unsupported"
            ),
        ),
        pytest.param(
            "list[int]",
            ["1", "2"],
            [1, 2],
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Builtin type unsupported"
            ),
        ),
        (
            typing.List,
            ["a", "b"],
            ["a", "b"],
        ),
        (
            typing.List[int],
            ["1", "2"],
            [1, 2],
        ),
    ),
)
def test_list_types(monkeypatch, list_type, input_value, expected):
    captured_a = None
    captured_b = None
    args = [""] + input_value + ["--b"] + input_value
    monkeypatch.setattr("argparse._sys.argv", args)

    # not sure how else to do this to test on < 3.9
    if type(list_type) == str:
        list_type = eval(list_type)

    @command
    def func(a: list_type, b: list_type = None):
        nonlocal captured_a
        nonlocal captured_b
        captured_a = a
        captured_b = b

    func()

    assert captured_a == expected
    assert captured_a == expected


def test_register_other_types(monkeypatch):
    captured_foo = None
    monkeypatch.setattr("argparse._sys.argv", ["", "a-b"])

    @dataclass
    class CustomType:
        a: str
        b: str

    def custom_type_factory(input_str: str) -> CustomType:
        return CustomType(*input_str.split("-"))

    @command(param_factories={CustomType: custom_type_factory})
    def func(foo: CustomType):
        nonlocal captured_foo
        captured_foo = foo

    func()

    assert captured_foo == CustomType("a", "b")


def test_enum_choices_valid_argument(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "first"])

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: Choices):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == Choices.FIRST


def test_enum_choices_multiple_valid_arguments(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "first", "second"])

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: typing.List[Choices]):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == [Choices.FIRST, Choices.SECOND]


def test_enum_choices_invalid_argument(monkeypatch, capsys):
    def raise_an_exception(_):
        raise Exception()

    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["prog", "invalid"])
    monkeypatch.setattr("argparse._sys.exit", raise_an_exception)
    monkeypatch.setattr(
        "shutil.get_terminal_size", lambda: os.terminal_size((1000, 1000))
    )

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: Choices):
        nonlocal captured_a
        captured_a = a

    with pytest.raises(Exception):
        func()

    assert (
        capsys.readouterr().err
        == """\
usage: prog [-h] a
prog: error: argument a: invalid choice: 'invalid' (choose from 'first', 'second')
"""
    )


def test_subcommand(monkeypatch):
    captured_global_option = None
    captured_foo = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--global-option", "subfunc", "bar"])

    @command
    def func(global_option: bool = False):
        ...

    @func.subcommand
    def subfunc(foo, **kwargs):
        nonlocal captured_global_option
        nonlocal captured_foo
        captured_global_option = kwargs["global_option"]
        captured_foo = foo

    func()

    assert captured_global_option is True
    assert captured_foo == "bar"


def test_main_command_with_subcommand(monkeypatch):
    captured_global_option = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--global-option"])

    @command
    def func(global_option: bool = False):
        nonlocal captured_global_option
        captured_global_option = global_option

    @func.subcommand
    def subfunc(foo, **kwargs):
        ...

    func()

    assert captured_global_option is True


def test_subcommand_can_be_called_directly():
    captured_bar = None

    @command
    def parent():
        ...

    @subcommand(parent)
    def foo(bar):
        nonlocal captured_bar
        captured_bar = bar

    foo("buzz")

    assert captured_bar == "buzz"


def test_main_help_with_subcommands(monkeypatch, capsys):
    def raise_an_exception(_):
        raise Exception()

    monkeypatch.setattr("argparse._sys.argv", ["", "--help"])
    # raise an exception instead of exiting (or attempting to call func() with missing args)
    monkeypatch.setattr("argparse._sys.exit", raise_an_exception)

    @command
    def parent():
        ...

    @parent.subcommand
    def foo():
        ...

    @parent.subcommand
    def bar():
        ...

    with pytest.raises(Exception):
        parent()

    assert (
        capsys.readouterr().out
        == """\
usage: [-h] {foo,bar} ...

positional arguments:
  {foo,bar}
    foo
    bar

optional arguments:
  -h, --help  show this help message and exit
"""
    )
