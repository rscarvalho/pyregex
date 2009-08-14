# -*- coding: utf-8 -*-
from django.http import HttpRequest

class RegisterVars(dict):
    """
    This class provides a simplified mechanism to build context processors
    that only add variables or functions without processing a request.
    
    Your module should have a global instance of this class called 'register'.
    You can then add the 'register' variable as a context processor in your
    settings.py.
    
    How to use:
    
    >>> register = RegisterVars()
    >>> def func():
    ...     pass
    >>> register(func) # doctest:+ELLIPSIS
    <function func at ...>
    >>> @register
    ... def otherfunc():
    ...     pass
    >>> register['otherfunc'] is otherfunc
    True
    
    Alternatively you can specify the name of the function with either of:
    def func(...): ...
    register(func, 'new_name')
    
    @register('new_name')
    def ...
    
    You can even pass a dict or RegisterVars instance:
    register(othermodule.register)
    register({'myvar': myvar})
    """
    def __call__(self, item=None, name=None):
        # Allow for using a RegisterVars instance as a context processor
        if isinstance(item, HttpRequest):
            return self
        if name is None and isinstance(item, basestring):
            # @register('as_name') # first param (item) contains the name
            name, item = item, name
        elif name is None and isinstance(item, dict):
            # register(somedict)  or  register(othermodule.register)
            return self.update(item)
        if item is None and isinstance(name, basestring):
            # @register(name='as_name')
            return lambda func: self(func, name)
        self[name or item.__name__] = item
        return item
