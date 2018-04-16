parser_registry = {}


def register_parser(parser_key):
    def tags_decorator(func):
        parser_registry[parser_key] = func

        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return func_wrapper
    return tags_decorator


def get_parser_keys():
    return sorted(parser_registry.keys())
