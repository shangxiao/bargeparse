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
    captured_cc = None
    captured_dd = None
    captured_e = None
    monkeypatch.setattr(
        "argparse._sys.argv",
        ["", "--cc", "fizz", "--dd", "buzz", "-e", "bang", "foo", "bar"],
    )

    @command
    def func(a, b, cc=None, dd=None, e=None):
        nonlocal captured_a
        nonlocal captured_b
        nonlocal captured_cc
        nonlocal captured_dd
        nonlocal captured_e
        captured_a = a
        captured_b = b
        captured_cc = cc
        captured_dd = dd
        captured_e = e

    func()

    assert captured_a == "foo"
    assert captured_b == "bar"
    assert captured_cc == "fizz"
    assert captured_dd == "buzz"
    assert captured_e == "bang"


def test_keyword_only_args(monkeypatch):
    captured_aa = None
    captured_bb = None
    captured_cc = None
    monkeypatch.setattr("argparse._sys.argv", ["", "--aa", "foo", "--bb", "bar"])

    @command
    def func(*, aa, bb="b", cc="c"):
        nonlocal captured_aa
        nonlocal captured_bb
        nonlocal captured_cc
        captured_aa = aa
        captured_bb = bb
        captured_cc = cc

    func()

    assert captured_aa == "foo"
    assert captured_bb == "bar"
    assert captured_cc == "c"


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
        (bool, "--aa", True),
        (bool, "--no-aa", False),
        (date, "2000-01-01", date(2000, 1, 1)),
        (datetime, "2000-01-01 12:15:30", datetime(2000, 1, 1, 12, 15, 30)),
        (pathlib.Path, ".", pathlib.Path(".")),
    ),
)
def test_typehint(monkeypatch, input_type, input, expected):
    monkeypatch.setattr("argparse._sys.argv", ["", input])
    captured_aa = None

    @command
    def func(aa: input_type):
        nonlocal captured_aa
        captured_aa = aa

    func()

    assert captured_aa == expected


@pytest.mark.parametrize(
    "param_default,input,expected",
    (
        (False, "-a", True),
        (False, None, False),
        (True, "-a", False),
        (True, None, True),
    ),
)
def test_typehint_optional_boolean_single_char(
    monkeypatch, param_default, input, expected
):
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


@pytest.mark.parametrize(
    "param_default,input,expected",
    (
        (False, "--aa", True),
        (False, None, False),
        (True, "--aa", False),
        (True, None, True),
    ),
)
def test_typehint_optional_boolean(monkeypatch, param_default, input, expected):
    params = [""]
    if input:
        params += [input]
    monkeypatch.setattr("argparse._sys.argv", params)
    captured_aa = None

    @command
    def func(aa: bool = param_default):
        nonlocal captured_aa
        captured_aa = aa

    func()

    assert captured_aa == expected


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
    captured_bb = None
    args = [""] + input_value + ["--bb"] + input_value
    monkeypatch.setattr("argparse._sys.argv", args)

    # not sure how else to do this to test on < 3.9
    if type(list_type) == str:
        list_type = eval(list_type)

    @command
    def func(a: list_type, bb: list_type = None):
        nonlocal captured_a
        nonlocal captured_bb
        captured_a = a
        captured_bb = bb

    func()

    assert captured_a == expected
    assert captured_bb == expected


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
    captured_global_arg = None
    captured_global_option = None
    captured_foo = None
    monkeypatch.setattr(
        "argparse._sys.argv",
        ["", "global-argument", "--global-option", "subfunc", "bar"],
    )

    @command
    def func(global_argument, global_option: bool = False):
        ...

    @func.subcommand
    def subfunc(foo, *args, **kwargs):
        nonlocal captured_global_arg
        nonlocal captured_global_option
        nonlocal captured_foo
        captured_global_arg = args[0]
        captured_global_option = kwargs["global_option"]
        captured_foo = foo

    func()

    assert captured_global_arg == "global-argument"
    assert captured_global_option is True
    assert captured_foo == "bar"


def test_subcommand_without_var_args_or_var_kwargs(monkeypatch):
    captured_foo = None
    monkeypatch.setattr(
        "argparse._sys.argv",
        ["", "global-argument", "--global-option", "subfunc", "bar"],
    )

    @command
    def func(global_argument, global_option: bool = False):
        ...

    @func.subcommand
    def subfunc(foo):
        nonlocal captured_foo
        captured_foo = foo

    func()

    assert captured_foo == "bar"


def test_subcommand_also_as_command_with_no_args(monkeypatch):
    """
    An edge case where a subcommand was also a command but with no args
    """
    subfunc_run = False
    monkeypatch.setattr("argparse._sys.argv", ["", "subfunc"])

    @command
    def func():
        ...

    @command
    def subfunc():
        nonlocal subfunc_run
        subfunc_run = True

    func.subcommand(subfunc)

    func()

    assert subfunc_run


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
        aa,  # Help message for 'aa'
        # Not aa help message
        bb: str,  # Help message for 'bb'
        cc: str = 'Default for cc',  # Help message for 'cc'
        dd, ee,  # Help message for 'ee'
        ff, gg  # Help message for 'gg'
    ):
        def inner_func(
            aa,  # This should not be the help message for 'aa'
        ):
            ...
    # fmt: on

    with pytest.raises(ExitException):
        func()

    assert (
        capsys.readouterr().out
        == """\
usage: prog [-h] --aa AA --bb BB [--cc CC] --dd DD --ee EE --ff FF --gg GG

optional arguments:
  -h, --help  show this help message and exit
  --aa AA     Help message for 'aa' (required)
  --bb BB     Help message for 'bb' (required)
  --cc CC     Help message for 'cc' (default: Default for cc)
  --dd DD     (required)
  --ee EE     Help message for 'ee' (required)
  --ff FF     (required)
  --gg GG     Help message for 'gg' (required)
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
