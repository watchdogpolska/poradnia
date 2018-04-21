class JudgementsExceptions(Exception):
    pass


class ParseException(JudgementsExceptions):
    pass


class NotFoundAnyJudgementsException(ParseException):
    pass
