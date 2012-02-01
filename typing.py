# TYPER COMBAT  : A 2d typing game inspired by Typing of the Dead
# Travis J. Grathwell, Started August 8th, 2006

# Most all the graphics in this game are ripped from the game 'Gunstar Heroes' for the Sega Genesis. Used without permission.
# Other graphics have been purloined from Super Mario Bros., Pac-Man, Legend of Zelda.

import pygame, sys, time, string
from pygame.locals import *
from feeder import getFeeder
from general import *
from scene import MainGameScene, TitleScreen, GameOverScreen, ChallengeScreen, LoadingScreen
from opponents import Soldier, Copter, Ghost, Commando
from controller import Controller

if not pygame.font:
    print "Couldn't load font library, crashing hard"
    sys.exit(1)

def processEventsForKillSignal(events):
    for event in events:
        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            sys.exit()
    return events
    
def main(argv=sys.argv):
    if len(argv) == 2 and 640 <= int(argv[1]) <= 1280:
        game_constants.w, game_constants.h = (int(argv[1]), int(argv[1])*.75)
    else:
        game_constants.w, game_constants.h = (640,480)

    pygame.init()
    screen = pygame.display.set_mode((game_constants.w, game_constants.h))
    pygame.display.set_caption('Typer Combat')
    pygame.mouse.set_visible(0)
    pygame.event.set_blocked(MOUSEMOTION)

    Word.font = GetFont(24)
    Score.font = GetFont(14)
    Platform.font = GetFont(16)

    loadImagesForAnimations()
    
    #Prepare Persistant Objects
    clock = pygame.time.Clock()
    directions = (K_UP, K_DOWN, K_LEFT, K_RIGHT)
    shifting = 0
    specials =         "1234567890[]\;',./"
    shifted_specials = "!@#$%^&*(){}|:\"<>?"
    special_keys_trans_table = string.maketrans(specials,shifted_specials)
     
    while True: # The Full Game Loop
        screen.set_clip()
        intro_screens = [TitleScreen(screen)]
        for basic_screen in intro_screens:
            event = None
            while basic_screen.showMe(): # Splashscreen Phase
                if event:
                    processEventsForKillSignal([event])
                    if event.type == KEYDOWN:
                        new_screen = basic_screen.handleEvent(event.key)
                        if new_screen: basic_screen = new_screen
                if basic_screen.dirty:
                    basic_screen.draw()
                event = pygame.event.wait()
        
        loading_scene = LoadingScreen(screen)
        loading_scene.draw()
        pygame.display.update()
        main_game_scene = MainGameScene(screen)
        
        starttime = time.time()
        player_movement = False

        # TODO: dynamically choose which feeds based on options        
        # if DEBUG:
        #     feed_sources = [getFeeder(x) for x in options_screen.getFeedOptions()]
        #     # Eval a string like 'Copter' into its class object (brittle, refactor)
        #     spawners = [eval(enemy) for enemy in options_screen.getEnemyOptions()]

        feed_sources = [getFeeder('Google'), getFeeder('Slashdot'), getFeeder('Digg')]
        spawners = [Soldier, Copter, Ghost]

        # need at least one feed
        if feed_sources == []:
            feed_sources = [getFeeder()]
            
        # vv TODO: fix these up, man what's going on here vv
        word_list = sum([feeder.words for feeder in feed_sources],[])
        sentence_list = sum([feeder.sentences for feeder in feed_sources],[])

        words = WordMaker(word_list)
        sentences = WordMaker(sentence_list)
        controller = Controller(main_game_scene,words,sentences)
        
        main_game_scene.redraw()
        pygame.display.update()
        while main_game_scene.showMe(): # Real game phase
            elapsed = time.time() - starttime + 1 # Prevent divide by zero errors the cheater's way
            clock.tick(60)
            
            if main_game_scene.challenging: # if we're fighting a commando, trap events
                challenge_screen = ChallengeScreen(screen, controller.sentences.next())
                while challenge_screen.showMe():
                    challenge_screen.draw()
                    for event in processEventsForKillSignal(pygame.event.get()):
                        if event.type == KEYDOWN:
                            if event.key == K_RETURN:
                                challenge_screen.showing = False
                                main_game_scene.movelist = [] #fixme - hack to remove bug when moving manually into a challenge
                                main_game_scene.exitChallenge()
                    pygame.display.update()
            
            #Handle Input Events for main game scene
            for event in processEventsForKillSignal(pygame.event.get()):
                if event.type == KEYDOWN:
                    if event.key in (K_LCTRL,K_RCTRL): # Release selected object
                        controller.unselect()
                    elif event.key in (K_LSHIFT,K_RSHIFT): # Note that shift is being pressed
                        shifting += 1
                    elif event.key == K_SPACE: # Jump
                        if player_movement: main_game_scene.player.jump()
                        else: controller.change_direction()
                    elif event.key in directions: # Directional pad movement
                        if player_movement: main_game_scene.movelist.append(event.key)
                    elif event.key == K_END: # Toggle player control (for debugging)
                        player_movement = not player_movement
                    elif event.key in range(256): # Typing an ASCII character
                        if chr(event.key) in string.lowercase: # Typing a word
                            controller.type_normal(chr(event.key))
                        elif chr(event.key) in specials+shifted_specials: # Typing a special character
                            if not shifting: controller.type_special(chr(event.key))
                            else: controller.type_special(chr(event.key).translate(special_keys_trans_table))
                elif event.type == KEYUP:
                    if event.key in directions:
                        if player_movement: main_game_scene.movelist.remove(event.key)
                    elif event.key in (K_LSHIFT,K_RSHIFT):
                        shifting -= 1

            # Timekeeping
            if not player_movement: controller.tick()
            controller.tock(spawners) # This function spawns enemies every random-interval-or-so.
            main_game_scene.tick(elapsed)
            
            #Drawing
            dirty = main_game_scene.draw()
            pygame.display.update(dirty)
            
        # Clear any clip state from main game phase
        screen.set_clip()
            
        game_over_screen = GameOverScreen(screen)
        event = None
        while game_over_screen.showMe(): # Endgame Screen Phase
            if event:
                processEventsForKillSignal([event])
                if event.type == KEYDOWN:
                    if event.key == K_RETURN: # Choose whether to restart
                        game_over_screen.handleEvent(event.key)
            if game_over_screen.dirty:
                game_over_screen.draw() # Updates full screen, also
            event = pygame.event.wait()

if __name__ == '__main__':
    main()
