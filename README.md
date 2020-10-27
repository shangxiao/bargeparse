# bargeparse

Introspect function signatures to construct a CLI

```python
from bargeparse.command import command


@command
def sample_api(foo: int, bar, fizz="fizz", buzz=None):
    """
    This is a sample function!
    """
    print(f"{type(foo)} - {foo}")
    print(f"{type(bar)} - {bar}")
    print(f"{type(fizz)} - {fizz}")
    print(f"{type(buzz)} - {buzz}")


if __name__ == "__main__":
    sample_api()
```

produces:

```
$ main --help
usage: main.py [-h] [--fizz FIZZ] [--buzz BUZZ] foo bar

This is a sample function!

positional arguments:
  foo
  bar

optional arguments:
  -h, --help   show this help message and exit
  --fizz FIZZ
  --buzz BUZZ

$ main --fizz fizz --buzz buzz 1 2
<class 'int'> - 1
<class 'str'> - 2
<class 'str'> - fizz
<class 'str'> - buzz
```
