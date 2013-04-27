"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from unittest import TestCase
from torndb import Connection

class SimpleTest(TestCase):

    def setup(self):
        self.conn = Connection('localhsot', 'test', user='jpg', password='jpg')

    def test_create_branch(self):
        """
        Tests that 1 + 1 always equals 2.
        """

