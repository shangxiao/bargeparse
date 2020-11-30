import argparse


class BooleanOptionalAction(argparse.Action):
    """
    Direct copy of Python's argparse.BooleanOptionalAction for compatibility with pre-3.9
    """

    def __init__(
        self,
        option_strings,
        dest,
        default=None,
        type=None,
        choices=None,
        required=False,
        help=None,
        metavar=None,
    ):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if option_string.startswith("--"):
                option_string = "--no-" + option_string[2:]
                _option_strings.append(option_string)

        if help is not None and default is not None:
            help += f" (default: {default})"

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith("--no-"))


def enum_action_factory(enum_class):
    """
    Factory for a specific action to deal with enums.

    A specific action is required to manage enums that:
    a.) sets up choices based on the enum members' values;
    b.) converts to the enum after choice membership is checked in order to
        provide correct error messages.
    """

    class EnumAction(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            kwargs["choices"] = [member.value for member in enum_class]
            super().__init__(option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string):
            if isinstance(values, str):
                converted_values = enum_class(values)
            else:
                converted_values = [enum_class(value) for value in values]
            setattr(namespace, self.dest, converted_values)

    return EnumAction
