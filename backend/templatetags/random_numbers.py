import random
from django import template

register = template.Library()

@register.simple_tag
def random_int(a, b=None):
    if b is None:
        a, b = 0, a
    return random.randint(a, b)

@register.simple_tag
def random_str(a, b, p):
    if random.randint(0, p) != 0:
        return a
    else:
        return b