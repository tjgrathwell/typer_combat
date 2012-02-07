#!/usr/bin/env python

# TYPER COMBAT  : A 2d typing game inspired by Typing of the Dead
# Travis J. Grathwell, Started August 8th, 2006

# Most all the graphics in this game are ripped from the game 'Gunstar Heroes'
#   for the Sega Genesis. Used without permission.
# Other graphics taken from Super Mario Bros., Pac-Man, Legend of Zelda.

import pygame, sys, time
from pygame.locals import *
from general import game_constants, loadImagesForAnimations
from scene import TitleScreen

if not pygame.font:
    print "Couldn't load font library, crashing hard"
    sys.exit(1)

clock = pygame.time.Clock()

def processEventsForKillSignal(events):
    for event in events:
        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            sys.exit()
    return events

def game_loop(screen):
    events = []
    last_frame_time = None

    scene = TitleScreen(screen)

    while True:
        if not scene.lazy_redraw():
            clock.tick(60)
            events = pygame.event.get()

        for event in processEventsForKillSignal(events):
            if event.type == KEYDOWN:
                scene.handleKeydown(event.key)
            elif event.type == KEYUP:
                scene.handleKeyup(event.key)

        if scene.lazy_redraw():
            if scene.dirty:
                scene.draw()
            events = [pygame.event.wait()]
        else:
            elapsed = time.time() - last_frame_time if last_frame_time else .001

            scene.tick(elapsed)

            last_frame_time = time.time()

            dirty_rects = scene.draw()
            pygame.display.update(dirty_rects)

        screen.set_clip()

        new_scene = scene.switchToScene()
        if new_scene:
            scene = new_scene

def main(argv=sys.argv):
    if len(argv) == 2 and 640 <= int(argv[1]) <= 1280:
        game_constants.w, game_constants.h = (int(argv[1]), int(argv[1])*.75)
    else:
        game_constants.w, game_constants.h = (800,600)

    pygame.init()
    screen = pygame.display.set_mode((game_constants.w, game_constants.h))
    pygame.display.set_caption('Typer Combat')
    pygame.mouse.set_visible(0)
    pygame.event.set_blocked(MOUSEMOTION)

    loadImagesForAnimations()

    game_loop(screen)

if __name__ == '__main__':
    main()
