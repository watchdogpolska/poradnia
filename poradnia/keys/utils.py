import random
import string


def make_random_password(length=75):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))
