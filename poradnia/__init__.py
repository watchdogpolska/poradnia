__version__ = "1.0.1"


# Compatibility to eg. django-rest-framework
VERSION = tuple(
    int(num) if num.isdigit() else num
    for num in __version__.replace("-", ".", 1).split(".")
)


def get_version():
    return __version__


# TODO find chart.js usage and updated to v.4
