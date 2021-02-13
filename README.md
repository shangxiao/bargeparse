# bargeparse

![Tests](https://github.com/shangxiao/bargeparse/workflows/Tests/badge.svg)

Introspect function signatures to construct a CLI using [argparse](https://docs.python.org/3.9/library/argparse.html)


## Synopsis

Decorate your functions with `@bargeparse.command`...

```python
import bargeparse

@bargeparse.command
def awesome_cli(foo, bar=None):
    ...

if __name__ == "__main__":
    awesome_cli()
```

to produce a CLI :

```
python awesome_cli.py foo --bar bar
```


## Description

Bargeparse introspects your function signature using argparse to create a CLI with the following features:

* Type casting using typehints in the signature with special support for booleans and lists.
* Automatically create CLI "positional" or "optional" arguments from function parameters based on whether they have a
  default value; or whether they are positional-only or keyword-only.
* Choices via enums.
* Subcommands defined by separate functions.
* Help & usage messages as defined by argparse, using the function's docstring as the description and parameter comments
  for argument help messages.


## Installation

```
pip install bargeparse
```


## Mapping of Function Parameters to CLI Arguments

*Note: `argparse` uses the terminology "positional" to denote regular arguments passed to a command and "optional" to
denote arguments supplied as flags in either short or long format (eg `-h / --help`). Both argument types can be made to
be required or optional with `argparse`. `bargeparse` makes no attempt to force one way or the other and leaves that
choice up to the developer.*

Bargeparse automatically creates positional or optional CLI arguments based on the following observations about the
function siganture:
 * Parameters without a default value:
   * By default become positional arguments
   * Can be forced to become "required optional CLI arguments" by making them keyword-only
 * Parameters with a default:
   * By default become optional arguments
   * Can be forced to become "optional positional CLI arguments" by making them positional-only


## Type Casting with Type Hints

By default all arguments will be passed to the function as strings. Arguments may be cast to another type by specifying
the appropriate type hint.

The following types are supported out of the box:
  * `str`
  * `int`
  * `float`
  * `bool` (will always render as optional CLI arguments)
  * `date` (following the `%Y %m %d` format - delimited with any char)
  * `datetime` (following the `%Y %m %d %H %M %S` format - delimited with any char)
  * `list`, `list[T]`, `typing.List` and `typing.List[T]` where `T` is another supported type other than lists
  * enums
  * any type that can be invoked like a type factory as described in the [argparse
    docs](https://docs.python.org/3.9/library/argparse.html#type)

The last point means the following will produce an argument `foo` of type `CustomType`:

```python
@dataclass
class CustomType:
    value: str

@bargeparse.command
def cli(foo: CustomType):
    ...
```

### A note about lists & tuples

Single dimension lists & tuples are supported via the [`nargs="*"`
option](https://docs.python.org/3/library/argparse.html#nargs). As noted in the documentation:

> Note that it generally doesn’t make much sense to have more than one positional argument with `nargs='*'`, but multiple
> optional arguments with `nargs='*'` is possible.

Multi-optional arguments must be specified after positional arguments so that the CLI parser understands the boundaries
between the arguments.


## Parameter Help

Parameter help messages can be added by using comments.  Comments are linked to
the immediately preceding comment on the same line:

```python
@bargeparse.command
def cli(
    foo:  # Help message for foo
):
    ...
```


## Choices

[Choices](https://docs.python.org/3/library/argparse.html#choices) are supported through the use of enumerated types.
Although the argparse documentation mentions that the `choices` option supports enums, bargeparse does things a little
differently as [the default enum support is not very user-friendly](https://bugs.python.org/issue42501):

* The choices are listed as the enum's member values rather than the string representation of the members
* Choice membership is tested before converting to the enumerated type to allow argparse to give a better error message
  for invalid values.


## Subcommands

Sucommands are supported by registering their existence with the main command's through the `@bargeparse.subcommand`
decorator. To invoke the argparse parser for the main command and all subcommands simply run the main command.

A shortcut decorator is set on the main command's function for convenience.

```python
@bargeparse.command
def main_command(global_option: bool = False):
    """
    Documentation for main command
    """
    # ... code executed when no subcommand is specified

@main_command.subcommand
def subcommand(option: bool = False, **kwargs):
    """
    Documentation for subcommand
    """
    # ... global_option passed in through var args
```


## Usage

### A simple example

```python
@bargeparse.command
def sample_api(foo, bar=None):
    pprint(foo)
    pprint(bar)
```

produces:

```
$ python sample_api.py --help
usage: sample_api.py [-h] [--bar BAR] foo

positional arguments:
  foo

optional arguments:
  -h, --help  show this help message and exit
  --bar BAR

$ python sample_api.py 1 --bar 2
'1'
'2'
```


### Casting to integer

```python
@bargeparse.command
def sample_api(foo: int):
    pprint(foo)
```

```
$ python sample_api.py 1
1
```


### Casting to date

```python
@bargeparse.command
def sample_api(foo: date):
    pprint(foo)
```

```
$ python sample_api.py '2000-01-01'
datetime.date(2000, 1, 1)
```


### "Optional" positional CLI argument

Using positional-only function parameters we can make "optional" positional arguments that will take the default value if
nothing is supplied:

```python
@bargeparse.command
def sample_api(foo, bar=None, /):
    pprint(foo)
    pprint(bar)
```

```
$ python sample_api.py --help
usage: sample_api.py [-h] foo [bar]

positional arguments:
  foo
  bar

optional arguments:
  -h, --help  show this help message and exit

$ python sample_api.py fizz
'fizz'
None

$ python sample_api.py fizz buzz
'fizz'
'buzz'
```


### "Required" optional CLI argument

Using keyword-only function parameters we can make "required" optional arguments:

```python
@bargeparse.command
def sample_api(*, foo, bar=None):
    pprint(foo)
    pprint(bar)
```

```
$ python sample_api.py --help
usage: sample_api.py [-h] --foo FOO [--bar BAR]

optional arguments:
  -h, --help  show this help message and exit
  --foo FOO   required
  --bar BAR

$ python sample_api.py --foo fizz
'fizz'
None

$ python sample_api.py --foo fizz --bar buzz
'fizz'
'buzz'
```


### Boolean support

Booleans will always be rendered as optional CLI arguments:
 * Bools without a default value will be "required" and will have the following option format:
   * `--feature` to enable a feature
   * `--no-feature` to disable a feature
 * Bools with a default value will assume that default unless switched on (or off)


```python
@bargeparse.command
def sample_api(foo: bool, bar: bool = False):
    pprint(foo)
    pprint(bar)
```

```
$ python sample_api.py --help
usage: sample_api.py [-h] --foo [--bar]

optional arguments:
  -h, --help       show this help message and exit
  --foo, --no-foo  required
  --bar

$ python sample_api.py --foo
True
False

$ python sample_api.py --no-foo --bar
False
True
```


### List/Tuple support

Lists & tuples can be specified with any of the following:

 * `typing.List`
 * `typing.Tuple`
 * `typing.List[T]`
 * `typing.Tuple[T]`
 * `list`
 * `tuple`
 * `list[T]`
 * `tuple[T]`

Where `T` is another supported type other than a list or tuple.  Note that `list` and `tuple` are supported typehints
from Python 3.9 onwards.

When an optional argument is a list/tuple it should be specified after any positional arguments so as not to confuse the
parser.

```python
@bargeparse.command
def sample_api(foo: list, bar: list[int] = None):
    pprint(foo)
    pprint(bar)
```

```
$ python sample_api.py 1 2 --bar 1 2
['1', '2']
[1, 2]
```

```python
@bargeparse.command
def sample_api(foo: tuple, bar: tuple[int] = None):
    pprint(foo)
    pprint(bar)
```

```
$ python sample_api.py 1 2 --bar 1 2
('1', '2')
(1, 2)
```


### Parameter help

```python
@bargeparse.command
def sample_api(
    a,  # Help message for 'a'
    # A regular comment!
    b, c  # Help message for 'c'
):
    ...
```

```
$ python sample_api.py --help
usage: sample_api.py [-h] a b c

positional arguments:
  a           Help message for 'a'
  b
  c           Help message for 'c'

optional arguments:
  -h, --help  show this help message and exit
```


### Choices

```python
class Choices(enum.Enum):
    FIRST = "first"
    SECOND = "second"

@bargeparse.command
def sample_api(choice: Choices):
    pprint(choice)
```

```
$ python sample_api.py --help
usage: sample_api.py [-h] {first,second}

positional arguments:
  {first,second}

optional arguments:
  -h, --help      show this help message and exit

$ python sample_api.py invalid
usage: sample_api.py [-h] choice
sample_api.py: error: argument choice: invalid choice: 'invalid' (choose from 'first', 'second')

$ python sample_api.py first
<Choices.FIRST: 'first'>
```


### Subcommands

Note here that the first paragraph of the subcommand's docstring is assumed to be the summary and is used for the help
message for the subcommand in the main command's usage.

```python
@bargeparse.command
def main_command(global_option: bool = False):
    """
    Documentation for main command.
    """

@main_command.subcommand
def subcommand(option: bool = False, **kwargs):
    """
    Summary for subcommand.

    Longer description for subcommand.
    """
    pprint(option, kwargs)
```

```
$ python main_command.py --help
usage: main_command.py [-h] [--global-option] {subcommand} ...

Documentation for main command.

positional arguments:
  {subcommand}
    subcommand     Summary for subcommand.

optional arguments:
  -h, --help       show this help message and exit
  --global-option

$ python main_command.py subcommand --help
usage: main.py subcommand [-h] [--option]

Summary for subcommand.

Longer description for subcommand.

optional arguments:
  -h, --help  show this help message and exit
  --option

$ python main_command.py --global-option subcommand
False
{'global_option': True} 
```


### Docstring in the help message

```python
@bargeparse.command
def sample_api():
    """
    This is a sample function!
    """
```

```
$ python sample_api.py --help
usage: sample_api.py [-h]

This is a sample function!

optional arguments:
  -h, --help  show this help message and exit
```
