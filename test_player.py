#!/usr/bin/env python

import unittest
import player
import pygame

class testPlayer (unittest.TestCase):
    def setUp(self):
        # TODO: make it so this isn't needed!
        pygame.init()
        screen = pygame.display.set_mode((640, 480))

        initial_pos = (100, 100)
        self.player_instance = player.Player(initial_pos)

    def testInstantiation(self):
        self.assertEqual(self.player_instance.position, (100, 100))
        self.assertEqual(self.player_instance.direction, 'r')
        self.assertEqual(self.player_instance.jumpdir, 'u')

if __name__ == '__main__':
    unittest.main()
