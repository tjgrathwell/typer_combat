#!/usr/bin/env python

import unittest
import general
import pygame

class testWordMaker (unittest.TestCase):
    def setUp(self):
        # TODO: make it so this isn't needed!
        pygame.init()
        screen = pygame.display.set_mode((640, 480))

        self.wordmaker = general.WordMaker([
          'abracadabra',
          'badracaladra',
          'alphabet',
        ])

    def testInstantiation(self):
        # Never return words that start with the characters passed in to next_word.
        a_and_b = [self.wordmaker.next_word() for _ in xrange(100)]
        self.assertEqual(set([word.string[0] for word in a_and_b]), set(['a', 'b']))

        only_b  = [self.wordmaker.next_word(['a']) for _ in xrange(100)]
        self.assertEqual(set([word.string[0] for word in only_b]), set(['b']))

if __name__ == '__main__':
    unittest.main()
