from .local import Local  # noqa


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


class Test(Local):
    MIGRATION_MODULES = DisableMigrations()
