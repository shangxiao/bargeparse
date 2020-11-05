import sys

if sys.version_info <= (3, 8):
    collect_ignore = ["test_positional_only_parameters.py"]
