import random
import string

from django.utils.timezone import now


def prefix_gen(size=10, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))


def date_random_path(instance, filename):
    return 'letters/{y}/{m}/{d}/{r}/{f}'.format(y=now().year,
                                                m=now().month,
                                                d=now().day,
                                                r=prefix_gen(),
                                                f=filename[-75:])
