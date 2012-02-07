#!/usr/bin/env python

import unittest
import feeder

class testFeeder (unittest.TestCase):
    def setUp(self):
        self.feeder = feeder.getFeeder()

    def testWordIsGood(self):
        self.assertFalse(self.feeder.wordIsGood('hat')) # too short
        self.assertFalse(self.feeder.wordIsGood('border="0"')) # only lowercase is good

        self.assertTrue(self.feeder.wordIsGood('hats'))
        self.assertTrue(self.feeder.wordIsGood('abracadabra'))

if __name__ == '__main__':
    unittest.main()
