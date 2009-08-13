# -*- coding: utf-8 -*-
from django.test import TestCase
from google.appengine.ext import db
from pyutils import object_list_to_table, equal_lists
import os

class ModelTestCase(TestCase):
    """
    A test case for models that provides an easy way to validate the DB
    contents against a given list of row-values.

    You have to specify the model to validate using the 'model' attribute:
    class MyTestCase(ModelTestCase):
        model = MyModel
    """
    def validate_state(self, columns, *state_table):
        """
        Validates that the DB contains exactly the values given in the state
        table. The list of columns is given in the columns tuple.

        Example:
        self.validate_state(
            ('a', 'b', 'c'),
            (1, 2, 3),
            (11, 12, 13),
        )
        validates that the table contains exactly two rows and that their
        'a', 'b', and 'c' attributes are 1, 2, 3 for one row and 11, 12, 13
        for the other row. The order of the rows doesn't matter.
        """
        current_state = object_list_to_table(columns,
            self.model.all())[1:]
        if not equal_lists(current_state, state_table):
            print 'DB state not valid:'
            print 'Current state:'
            print columns
            for state in current_state:
                print state
            print 'Should be:'
            for state in state_table:
                print state
            self.fail('DB state not valid')
