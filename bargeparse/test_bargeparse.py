import enum
import pathlib
import sys
import typing
from dataclasses import dataclass
from datetime import date, datetime

import pytest

from bargeparse import command, subcommand

from .conftest import ExitException


def test_command_no_params(monkeypatch):
    func_run = False
    monkeypatch.setattr("argparse._sys.argv", [""])

    @command
    def func():
        nonlocal func_run
        func_run = True

    func()

    assert func_run


def test_command_can_be_called_directly_bypassing_cli_parsing(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "wrong value"])

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
        pytest.param(
            tuple,
            ["a", "b"],
            ("a", "b"),
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Builtin type unsupported"
            ),
        ),
        pytest.param(
            "tuple[int]",
            ["1", "2"],
            (1, 2),
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Builtin type unsupported"
            ),
        ),
        (
            typing.Tuple,
            ["a", "b"],
            ("a", "b"),
        ),
        (
            typing.Tuple[int],
            ["1", "2"],
            (1, 2),
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


def test_enum_choices_multiple_valid_arguments_using_tuple(monkeypatch):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["", "first", "second"])

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: typing.Tuple[Choices]):
        nonlocal captured_a
        captured_a = a

    func()

    assert captured_a == (Choices.FIRST, Choices.SECOND)


def test_enum_choices_invalid_argument(prepare_for_output, monkeypatch, capsys):
    captured_a = None
    monkeypatch.setattr("argparse._sys.argv", ["prog", "invalid"])

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: Choices):
        nonlocal captured_a
        captured_a = a

    with pytest.raises(ExitException):
        func()

    assert (
        capsys.readouterr().err
        == """\
usage: prog [-h] {first,second}
prog: error: argument a: invalid choice: 'invalid' (choose from 'first', 'second')
"""
    )


def test_enum_choices_help(prepare_for_output, monkeypatch, capsys):
    monkeypatch.setattr("argparse._sys.argv", ["prog", "--help"])

    class Choices(enum.Enum):
        FIRST = "first"
        SECOND = "second"

    @command
    def func(a: Choices):
        ...

    with pytest.raises(ExitException):
        func()

    assert (
        capsys.readouterr().out
        == """\
usage: prog [-h] {first,second}

positional arguments:
  {first,second}

optional arguments:
  -h, --help      show this help message and exit
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


def test_main_help_with_subcommands_only_shows_summary(
    prepare_for_output, monkeypatch, capsys
):
    monkeypatch.setattr("argparse._sys.argv", ["prog", "--help"])

    @command
    def parent():
        ...

    @parent.subcommand
    def foo():
        """
        Foo summary
        split over multiple lines.

        Longer foo description.
        """
        ...

    @parent.subcommand
    def bar():
        ...

    with pytest.raises(ExitException):
        parent()

    assert (
        capsys.readouterr().out
        == """\
usage: prog [-h] {foo,bar} ...

positional arguments:
  {foo,bar}
    foo       Foo summary split over multiple lines.
    bar

optional arguments:
  -h, --help  show this help message and exit
"""
    )


def test_subcommand_description(prepare_for_output, monkeypatch, capsys):
    monkeypatch.setattr("argparse._sys.argv", ["prog", "foo", "--help"])

    @command
    def parent():
        ...

    @parent.subcommand
    def foo():
        """
        Foo summary
        split over multiple lines.

        Longer foo description.
        """
        ...

    with pytest.raises(ExitException):
        parent()

    assert (
        capsys.readouterr().out
        == """\
usage: prog foo [-h]

Foo summary
split over multiple lines.

Longer foo description.

optional arguments:
  -h, --help  show this help message and exit
"""
    )


def test_parameter_help(prepare_for_output, monkeypatch, capsys):
    monkeypatch.setattr("argparse._sys.argv", ["prog", "--help"])

    # fmt: off
    @command
    def func(
        *,
        a,  # Help message for 'a'
        # Not a help message
        b: str,  # Help message for 'b'
        c: str = 'Default for c',  # Help message for 'c'
        d, e,  # Help message for 'e'
        f, g  # Help message for 'g'
    ):
        def inner_func(
            a,  # This should not be the help message for 'a'
        ):
            ...
    # fmt: on

    with pytest.raises(ExitException):
        func()

    assert (
        capsys.readouterr().out
        == """\
usage: prog [-h] --a A --b B [--c C] --d D --e E --f F --g G

optional arguments:
  -h, --help  show this help message and exit
  --a A       Help message for 'a' (required)
  --b B       Help message for 'b' (required)
  --c C       Help message for 'c' (default: Default for c)
  --d D       (required)
  --e E       Help message for 'e' (required)
  --f F       (required)
  --g G       Help message for 'g' (required)
"""
    )


def test_force_print_help(monkeypatch, capsys):
    """
    If the command declares **kwargs then pass the argparse parser for convenience.
    """
    monkeypatch.setattr("argparse._sys.argv", ["prog", "foo"])

    @command
    def func(foo, **kwargs):
        kwargs["parser"].print_help()

    func()

    assert (
        capsys.readouterr().out
        == """\
usage: prog [-h] foo

positional arguments:
  foo

optional arguments:
  -h, --help  show this help message and exit
"""
    )


def test_parser_customisation(monkeypatch):
    captured_foo = None
    captured_bar = None
    captured_buzz = None
    monkeypatch.setattr(
        "argparse._sys.argv", ["", "foo1", "foo2", "bar", "--buzz", "buzz"]
    )

    @command
    def wrapper(parser):
        parser.add_argument("foo", nargs=2)

        def func(bar, buzz=None, **kwargs):
            nonlocal captured_foo
            nonlocal captured_bar
            nonlocal captured_buzz
            captured_foo = kwargs["foo"]
            captured_bar = bar
            captured_buzz = buzz

        return func

    wrapper()

    assert captured_foo == ["foo1", "foo2"]
    assert captured_bar == "bar"
    assert captured_buzz == "buzz"
