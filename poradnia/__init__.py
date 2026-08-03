<<<<<<< HEAD
__version__ = "1.7.31"
=======
__version__ = "1.7.29"
>>>>>>> origin/fix_issues


# Compatibility to eg. django-rest-framework
VERSION = tuple(
    int(num) if num.isdigit() else num
    for num in __version__.replace("-", ".", 1).split(".")
)


def get_version():
    return __version__
