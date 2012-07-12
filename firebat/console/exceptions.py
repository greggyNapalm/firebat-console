# -*- coding: utf-8 -*-

"""
firebat.console.exeptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Exception classes related with config files
"""


class StepperAmmoFormat(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        #return repr(self.value)
        return self.value


class StepperSchemaFormat(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        #return repr(self.value)
        return self.value
