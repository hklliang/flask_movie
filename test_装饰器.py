# -*- coding:utf-8 -*-  
__author__ = 'hklliang'
__date__ = '2017-08-02 14:15'


from functools import wraps


def logged(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        print(func.__name__ + " was called")

        return func(*args, **kwargs)

    return with_logging


@logged
def f(x):
    """does some math"""
    return x + x * x

f(1)

# print(f.__name__)
  # prints 'f'
# print(f.__doc__ )
 # prints 'does some math'