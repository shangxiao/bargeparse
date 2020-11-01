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

* Type casting using typehints in the signature with special support for booleans.
* Automatically create CLI "positional" or "optional" arguments from function parameters based on whether they have a
  default value; or whether they are positional-only or keyword-only.
* Help & usage messages as defined by argparse, using the function's docstring as the description.


## Installation

```
pip install bargeparse
```


## Mapping of Function Parameters to CLI Arguments

*Note: `argparse` uses the uses the terminology "positional" to denote regular arguments passed to a command and "optional" to
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
