#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module convert VISA command to methods


For example, from a command like "BEGin:End VALue" the programm
will generate methods get_begin_end, set_begin_end and a property
begin_end using those methods.
"""
import re
import numbers

class TestValue(object):
    """Class use to test the paramters 

        This class implement the test method the return either None (if the test failed) or
        a string to format the value
    """
    def test(self, value):
        if self.condition(value):
            return self.to_string(value)
        else:
            return None
    def to_string(self, value):
        return str(value)
    def condition(self, value):
        return False

class TestValueFromType(TestValue):
    """ Test if a value is from a given type """
    def __init__(self, tpe):
        self.type = tpe
    def condition(self, value):
        return isinstance(value, self.type)
    def __repr__(self):
        return 'of type %s'%self.type.__name__

class TestValueFromRE(TestValue):
    """ Test a value using a regular expression """
    def __init__(self, re):
        self.re = re
    def condition(self, value):
        return re.match(value)
    def __repr__(self):
        return 'match %s'%self.re

class TestValueFromValue(TestValue):
    """ Test if a value is equal to a given one """
    def __init__(self, val):
        self.val = val
    def condition(self, value):
        return value==self.val
    def __repr__(self):
        return 'equal to %s'%self.val

def _short_version(s): 
    """Returns the short version of a string

    _short_version('COUPling')=='COUP'
    """
    sl = s.lower()
    return ''.join([c for i,c in enumerate(s) if s[i]<>sl[i]])

class TestValueFromString(TestValue):
    """ Test a value by comparing to a string. If the string is 
        CAPsmall then test for capsmall and cap. This test 
        is not case sensitive """
    def __init__(self, val):
        self.initial_val = val
        self.val = val.lower()
        self.val_short = _short_version(val).lower()
    def condition(self, value):
        return str(value).lower()==self.val or str(value).lower()==self.val_short
    def __repr__(self):
        return 'equal to %s or equal to %s'%(self.initial_val, self.val_short)

def _convert_value_to_TestValue(val):
    if isinstance(val, TestValue):
        return val
    elif isinstance(val, type):
        return TestValueFromType(val)
    elif isinstance(val, type(re.compile('po'))):
        return TestValueFromRe(val)
    elif isinstance(val, str) or isinstance(val, unicode):
        return TestValueFromString(val)
    else:
        return TestValueFromValue(val)

def _convert_list_value_to_list_of_TestValue(lst):
    return map(_convert_value_to_TestValue, lst)
    

def _try_to_convert_to_number(value):
    """Try to convert a string to a number (int or float)"""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

def _generic_get_command(cmd_name, out_conversion=None, doc=None):
    """ Create a method that will query the cmd_name 

        for example : _generic_get_command('CH1:IMPedance') will create the method 
        whose name is _get_ch1_impedance

        By default this function try also to convert the output of the request into an int or a float
        otherwise it uses the out_conversion function.
    """
    if out_conversion is None:
        out_conversion = _try_to_convert_to_number
    def get_val(self):
        value = self.ask('%s ?'%cmd_name)
        return out_conversion(value)
    get_val.__name__ = "_get_%s"%(cmd_name.replace(':','_').lower())
    get_val.__doc__ = get_val.__name__ if doc is None else doc
    return get_val

def _generic_set_command(cmd_name, list_value=None, default_value=None, doc=None):
    """ Create a method that will set the cmd_name 

        for example : _generic_set_command('CH1:IMPedance') will create the method 
        whose name is _set_ch1_impedance and takes one parameter

        Optional argument : 
                list_value : the list of possible values. The list can be direct value        
                        or type or regular expression. 
                default_value : the default value
    """
    if list_value is None:
        def set_val(self, value):
            self.write('%s %s'%(cmd_name, value))
    else:
        list_test_value = _convert_list_value_to_list_of_TestValue(list_value)
        def set_val(self, value=None):
            if value is None:
                value = default_value
                for test in list_test_value:
                a = test.test(value)
                if a is not None:
                    self.write('%s %s'%(cmd_name, a))
                    return None
            raise ValueError("Error in %s(). Set value is %s while it should be %s"\
                %('set_%s'%cmd_name.replace(':','_').lower(), value,  ' or '.join(map(str, list_test_value))) )
    set_val.__name__ = "_set_%s"%(cmd_name.replace(':','_').lower())
    set_val.__doc__ = set_val.__name__ if doc is None else doc
    return set_val


def generic_get_command(cmd_name, out_conversion=None, doc=None):
    cmd = _generic_get_command(cmd_name, out_conversion, doc=doc)
    return cmd

def generic_set_command(cmd_name, list_value=None, default_value=None, doc=None):
    cmd = _generic_set_command(cmd_name, list_value, default_value, doc=doc)
    return cmd

def generic_get_set_command(cls, cmd_name, list_value=None, default_value=None, out_conversion=None, doc=None):
    return generic_get_command(cmd_name, out_conversion=out_conversion, doc=doc),
                generic_set_command(cmd_name, list_value=list_value, default_value=default_value, doc=doc)

def _add_generic_get_command(cls, cmd_name, out_conversion=None, doc=None):
    cmd = _generic_get_command(cmd_name, out_conversion, doc=doc)
    setattr(cls, cmd.__name__[1:], cmd)
    setattr(cls, cmd.__name__, cmd)
    pretty_name = cmd_name.replace(':','_').lower()
    setattr(cls, '_'+pretty_name, property(getattr(cls, '_get_'+pretty_name), doc=doc))
    setattr(cls, pretty_name, property(getattr(cls, 'get_'+pretty_name), doc=doc))
def _add_generic_set_command(cls, cmd_name, list_value=None, default_value=None, doc=None):
    cmd = _generic_set_command(cmd_name, list_value, default_value, doc=doc)
    setattr(cls, cmd.__name__[1:], cmd)
    setattr(cls, cmd.__name__, cmd)
def _add_generic_get_set_command(cls, cmd_name, list_value=None, default_value=None, out_conversion=None, doc=None):
    _add_generic_get_command(cls, cmd_name, out_conversion, doc=doc)            
    _add_generic_set_command(cls, cmd_name, list_value, default_value, doc=doc)            
    pretty_name = cmd_name.replace(':','_').lower()
    setattr(cls, '_'+pretty_name, property(getattr(cls, '_get_'+pretty_name), getattr(cls, '_set_'+pretty_name), doc=doc))
    setattr(cls, pretty_name, property(getattr(cls, 'get_'+pretty_name), getattr(cls, 'set_'+pretty_name), doc=doc))

if __name__ == "__main__":
    class Generic(object):
        def write(self,s):
            print s
        def ask(self,s):
            print s
            return '45.4'
    class Test(Generic):
        pass
    _add_generic_get_set_command(Test, 'COUCOU:VAL',["PIErre", "MATHilde", numbers.Number], default_value='Pierre', doc='This is a test method')
