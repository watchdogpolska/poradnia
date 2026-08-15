__version__ = "1.8.41"


# Compatibility to eg. django-rest-framework
VERSION = tuple(
    int(num) if num.isdigit() else num
    for num in __version__.replace("-", ".", 1).split(".")
)


def get_version():
    return __version__
