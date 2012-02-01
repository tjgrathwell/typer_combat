import pygame, random
from pygame.locals import *
from player import Player
from general import game_constants, SpecialChars, RenderUpdatesDraw, Box, Platform, Score, Word, GetFont, loadframes, Color
from opponents import Soldier, Copter, Ghost, Commando

def is_reachable(object, player_rect, statics):
    """ Is it possible for the player to jump to this platform in the concievable future """
    # Test 1: the platform must be within jumping height
    if player_rect.bottom - game_constants.maxjump_height < object.rect.top < player_rect.bottom:
        # Test 2: the player cannot be under the platform
        if (player_rect.right < object.rect.left):
            # Test 3: the path from the player position to the optimal jump position must be contiguous
            jumpdist = object.rect.left - player_rect.right
            if jumpdist < game_constants.maxjump_width: # Maximum distance that can be jumped
                return True
            else:
                start = (player_rect.right, player_rect.bottom)
                size = (jumpdist - game_constants.maxjump_width, 1)
                testrect = pygame.rect.Rect(start, size)
                for collider in statics:
                    if collider.rect.contains(testrect):
                        return True
        elif (player_rect.left > object.rect.right):
            # Test 3: the path from the player position to the optimal jump position must be contiguous
            jumpdist = player_rect.left - object.rect.right
            if jumpdist < game_constants.maxjump_width: # Maximum distance that can be jumped
                return True
            else:
                start = (object.rect.right + game_constants.maxjump_width, player_rect.bottom)
                size = (jumpdist - game_constants.maxjump_width, 1)
                testrect = pygame.rect.Rect(start, size)
                for collider in statics:
                    if collider.rect.contains(testrect):
                        return True

class Health:
    """ Show hearts in a corner of the screen """

    def __init__(self, max_hearts):
        import os
        self.full = pygame.image.load(os.path.join('.', 'data', 'assorted', 'heartfull.gif')).convert_alpha()
        self.full = pygame.transform.scale(self.full, (self.full.get_width() * 2, self.full.get_height() * 2))
        self.empty = pygame.image.load(os.path.join('.', 'data', 'assorted', 'heartempty.gif')).convert_alpha()
        self.empty = pygame.transform.scale(self.empty, (self.empty.get_width() * 2, self.empty.get_height() * 2))
        
        self.rect = pygame.rect.Rect((0, 0), (0, 0))
        self.max_hearts = max_hearts
        self.current_hearts = max_hearts
        self.redraw = True

    def clear(self, screen, background):
        if self.redraw: # The line below is way slow, why?!
            screen.blit(background, self.rect)
    def draw(self, screen):
        if self.redraw:
            lastx = 5
            dirty = []
            for _ in xrange(self.current_hearts): # Full hearts
                dirty += [screen.blit(self.full, self.full.get_rect(left = lastx, top = 5))]
                lastx = lastx + self.full.get_width() + 2
            for _ in xrange(self.current_hearts, self.max_hearts): # Empty hearts
                dirty += [screen.blit(self.empty, self.empty.get_rect(left = lastx, top = 5))]
                lastx = lastx + self.empty.get_width() + 2
                
            self.rect = dirty[0].unionall(dirty[1:])
            self.redraw = False
            return dirty
        else:
            return []
    def fill(self):
        self.current_hearts = self.max_hearts
        self.redraw = True

    def empty(self):
        self.current_hearts = 0
        self.redraw = True

    def increase(self):
        if self.current_hearts != self.max_hearts:
            self.current_hearts += 1
            self.redraw = True

    def decrease(self):
        if self.current_hearts != 0:
            self.current_hearts -= 1
            self.redraw = True

    def value(self):
        return self.current_hearts
             
class LoadingScreen:
    def __init__(self, screen):
        self.dirty = True
        self.screen = screen
        self.showing = True

    def draw(self):
        self.screen.fill((0, 0, 0))
        message = GetFont(72).render("Loading...", 1, Color.MOSTLY_WHITE)
        self.screen.blit(message, message.get_rect(centerx = self.screen.get_width() / 2, centery = self.screen.get_height() * .25))
        pygame.display.update()
        
        self.dirty = False
                        
class GameOverScreen:
    def __init__(self, screen):
        self.dirty = True
        self.screen = screen
        self.showing = True

    def draw(self):
        self.screen.fill((0, 0, 0))
        message = GetFont(72).render("GAME OVER", 1, Color.MOSTLY_WHITE)
        instr = GetFont(32).render("Return to restart, Esc to quit.", 1, Color.MOSTLY_WHITE)
        self.screen.blit(message, message.get_rect(centerx = self.screen.get_width() / 2, centery = self.screen.get_height() * .25))
        self.screen.blit(instr, instr.get_rect(centerx = self.screen.get_width() / 2, centery = self.screen.get_height() * .75))
        pygame.display.update()
        
        self.dirty = False
        
    def handleEvent(self, event_key):
        if event_key == K_RETURN:
            self.showing = False
        
    def showMe(self):
        return self.showing
                   
class TitleScreen:
    def __init__(self, screen):
        self.dirty = True
        self.screen = screen
        self.showing = True
        self.options_order = ['play', 'instructions', 'options']
        self.selected_option = 0

    def draw(self):
        self.screen.fill((50, 50, 50))
        title = GetFont(50).render("TYPER COMBAT", 1, Color.MOSTLY_WHITE)
        title_rect = title.get_rect(centerx = game_constants.w / 2, top = 0)
        self.screen.blit(title, title_rect) 

        options_texts = []
        for i, option_str in enumerate(self.options_order):
            color = Color.MOSTLY_WHITE
            if (i == self.selected_option):
                color = Color.YELLOW
            options_texts.append(GetFont(24).render(option_str.upper(), 1, color))

        draw_h = game_constants.h / 2
        for option in options_texts:
            rect = option.get_rect(centerx = game_constants.w / 2, top = draw_h)
            self.screen.blit(option, rect)
            draw_h += rect.height

        pygame.display.update()
        self.dirty = False
        
    def handleEvent(self, event_key):
        if event_key == K_UP:
            self.selected_option = max(self.selected_option - 1, 0)
            self.dirty = True
        if event_key == K_DOWN:
            self.selected_option = min(self.selected_option + 1, len(self.options_order))
            self.dirty = True
        if event_key == K_RETURN:
            selected_op = self.options_order[self.selected_option]
            if (selected_op == 'play'):
                self.showing = False
            if (selected_op == 'instructions'):
                return InstructionsScreen(self.screen)
            if (selected_op == 'options'):
                return OptionsScreen(self.screen)
        return None
        
    def showMe(self):
        return self.showing
                 
class InstructionsScreen:
    def __init__(self, screen):
        self.dirty = True
        self.screen = screen

        self.image = loadframes('gunstar',   ('gunside1.png',))[0]
        self.image = pygame.transform.scale2x(pygame.transform.scale2x(self.image)) # x4!
        
        self.soldier = loadframes('soldier', ('rest1.gif',))[0]
        self.chopper = loadframes('copter',  ('fly1.gif',))[0]
        self.ghost   = loadframes('ghost',   ('right1.gif',))[0]

        self.showing = True

    def draw(self):
        self.screen.fill((50, 50, 50))

        enemy_list_text = """SOLDIERS are constrained by the laws of gravity.
COPTERS can fly, but won't go through platforms.
GHOSTS can phase through platforms."""
        enemy_list = [GetFont(16).render(text, 1, Color.MOSTLY_WHITE) for text in reversed(enemy_list_text.split("\n"))] 
        
        instructions_text = """Type the words that appear over enemies to defeat them.
Type the character that appears on a platform to jump to it.
Press CTRL to deselect a word.
Press space to turn around.
Press return to continue."""
        instructions = [GetFont(16).render(text, 1, Color.MOSTLY_WHITE) for text in reversed(instructions_text.split("\n"))] 
        
        last = game_constants.h
        for text in (instructions):
            this = last - text.get_height()
            self.screen.blit(text, text.get_rect(centerx = game_constants.w / 2, centery = this))
            last = this
            
        for text, image in zip(enemy_list, (self.ghost, self.chopper, self.soldier)):
            this = last - text.get_height() - 20
            rect = text.get_rect(centerx = game_constants.w / 2, centery = this)
            self.screen.blit(text, rect)
            self.screen.blit(image, image.get_rect(centerx = rect.left - image.get_width() - 10, centery = this))
            last = this
       
        gunstar_top = (last) / 2 - self.image.get_height() / 2
        self.screen.blit(self.image, self.image.get_rect(centerx = game_constants.w / 2, top = gunstar_top))     
       
        pygame.display.update()
        self.dirty = False
        
    def handleEvent(self, event_key):
        if event_key == K_RETURN:
            self.showing = False
        
    def showMe(self):
        return self.showing
        
class Option:
    def __init__(self, screen, value, checked = False, active = False):
        self.screen = screen
        self.checked = checked
        self.active = active
        self.value = value

    def toggle(self):
        self.checked = not self.checked

    def is_checked(self):
        return self.checked

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def draw(self, (x, y)):
        text_line = GetFont(16).render(self.value, 1, Color.MOSTLY_WHITE)
        text_line_rect = text_line.get_rect(left = x + 30, top = y)
        self.screen.blit(text_line, text_line_rect)
        
        outer_rect = Rect(x, y, 25, 25)
        inner_rect = outer_rect.inflate(-8, -8)
        
        if self.checked:
            if self.active: # Selected with cursor: box with box in it
                pygame.draw.rect(self.screen, Color.LIGHT_GRAY, outer_rect, 0)
                pygame.draw.rect(self.screen, Color.GRAY, inner_rect, 0)
            else: # Selected without cursor: tiny box
                pygame.draw.rect(self.screen, Color.BLACK, outer_rect, 0)
                pygame.draw.rect(self.screen, Color.GRAY, inner_rect, 0)
        else:
            if self.active: # Unselected with cursor: empty box
                pygame.draw.rect(self.screen, Color.LIGHT_GRAY, outer_rect, 0)
                pygame.draw.rect(self.screen, Color.BLACK, inner_rect, 0)
            else: # Unselected without cursor: blank
                pygame.draw.rect(self.screen, Color.DARK_GRAY, outer_rect, 0)

class OptionGroup:
    def __init__(self, (x, y), options = []):
        self.options = options
        self.x = x
        self.y = y
        self.selected = 0

    def up(self):
        if self.selected > 0:
            self.options[self.selected].deactivate()
            self.selected -= 1
            self.options[self.selected].activate() 

    def down(self):
        if self.selected < len(self.options) - 1:
            self.options[self.selected].deactivate()
            self.selected += 1
            self.options[self.selected].activate()

    def select(self):
        self.options[self.selected].toggle()

    def activate(self):
        self.options[self.selected].activate()

    def deactivate(self):
        self.options[self.selected].deactivate()

    def add(self, option):
        self.options.append(option)

    def draw(self):
        for i, option in enumerate(self.options):
            option.draw((self.x, self.y + 25 * i))

    def get_checked(self):
        return [opt for opt in self.options if opt.is_checked()]
        
class OptionsScreen:
    def __init__(self, screen, word_sources = [], enemy_types = []):
        self.dirty = True
        self.screen = screen
        self.showing = True

        # TODO does this belong somewhere else?
        self.word_sources = ['Google','Digg','Slashdot']
        self.enemy_types = [Soldier, Copter, Ghost, Commando]
        
        self.options = self.word_sources + [x.name for x in self.enemy_types]
        self.feeds_group = OptionGroup((100, 100), [Option(self.screen, word) for word in self.word_sources])
        self.enemy_group = OptionGroup((300, 100), [Option(self.screen, x.name) for x in self.enemy_types])
        self.option_groups = [self.feeds_group, self.enemy_group]
        self.feeds_group.activate()
        
        self.groupnum = 0
        
    def draw(self):
        self.screen.fill((50, 50, 50))
        text_line = GetFont(16).render("INTENSE OPTIONS SCREEN", 1, Color.MOSTLY_WHITE)
        text_line_rect = text_line.get_rect(centerx = game_constants.w / 2, top = 0)
        self.screen.blit(text_line, text_line_rect)
        
        [group.draw() for group in self.option_groups] 
        
        text_line = GetFont(16).render("(Space to select, return to continue)", 1, Color.MOSTLY_WHITE)
        text_line_rect = text_line.get_rect(centerx = game_constants.w / 2, bottom = game_constants.h)
        self.screen.blit(text_line, text_line_rect)
        
        pygame.display.update()
        self.dirty = False

    def handleEvent(self, event_key):
        if event_key == K_RETURN:
            self.showing = False
        elif event_key == K_DOWN:
            self.option_groups[self.groupnum].down()
        elif event_key == K_UP:
            self.option_groups[self.groupnum].up()
        elif event_key == K_LEFT:
            if self.groupnum > 0:
                self.option_groups[self.groupnum].deactivate()
                self.groupnum -= 1
                self.option_groups[self.groupnum].activate()
        elif event_key == K_RIGHT:
            if self.groupnum < len(self.option_groups) - 1:
                self.option_groups[self.groupnum].deactivate()
                self.groupnum += 1
                self.option_groups[self.groupnum].activate()
            self.option_groups[self.groupnum].activate()
        elif event_key == K_SPACE:
            self.option_groups[self.groupnum].select()
        self.dirty = True

    def showMe(self):
        return self.showing
    
    def getFeedOptions(self):
        return [opt.value for opt in self.feeds_group.get_checked()]
    
    def getEnemyOptions(self):
        return [opt.value for opt in self.enemy_group.get_checked()]
                        
class MainGameScene:
    """ Overarching, badly-structured class controlling the current game environment, mostly. """
    def __init__(self, screen):
        self.headersize = 30
    
        self.camera = pygame.rect.Rect(0, 0, game_constants.w, game_constants.h)
        self.screen = screen
        self.special_chars = SpecialChars()
        self.movelist = []
        self.time_elapsed = 0
        
        self.health = Health(5)
        self.score = Score(screen)
        self.player = Player((screen.get_width() / 2, screen.get_height() / 2 - 30))
        self.playergroup = RenderUpdatesDraw(self.player)

        self.challenge = False # Draw "TYPING CHALLENGE" screen
        self.platforms = {game_constants.h - 80 : [Box(-10000, game_constants.h - 80, 20000, 16)]}
        self.statics = RenderUpdatesDraw()
        self.statics.add(self.platforms.values()[0])
        self.screenstatics = RenderUpdatesDraw()
        self.actives = RenderUpdatesDraw()
        self.powerups = RenderUpdatesDraw()

        self.place_platforms()
        self.player.colliders = self.screenstatics
        
        self.header = pygame.Surface((screen.get_width(), self.headersize))
        self.header.fill((0, 0, 0))
        
        self.background = pygame.Surface(screen.get_size()).convert()

        gradiation = 128.0
        for i in xrange(int(gradiation)):
            color = (150 - (i * 150 / gradiation), 150 - (i * 150 / gradiation), 200)
            rect = (0, i * game_constants.h / gradiation, game_constants.w, game_constants.h / gradiation + 1)
            self.background.fill(color, rect)

        self.screencheck() # Move sprites into or out of 'screenstatics' group based on whether they're in camera

        # fixme: rearchitect this
        self.challenging = False
        self.showing = True
        
    def place_platforms(self):
        def fill_level(height, camera):
            platform_level = self.platforms.setdefault(height, [])

            max_right = camera.right + game_constants.w
            min_left = camera.left - game_constants.w
        
            # cull platforms that have gone too far -- TODO this doesn't work yet
            bad_platforms = [p for p in platform_level if p.rect.left > max_right or p.rect.right < min_left]
            [platform_level.remove(p) for p in bad_platforms]
            [self.statics.remove(p) for p in bad_platforms]
            
            # add on platforms until the limit is reached
            if not len(platform_level):
                leftmost = random.randint(-game_constants.w, game_constants.w)
                rightmost = leftmost = random.randint(-game_constants.w, game_constants.w)
            else:
                leftmost = min([p.rect.left for p in platform_level])
                rightmost = max([p.rect.right for p in platform_level])

            while rightmost < max_right:
                new_start = rightmost + random.randint(150, 300)
                new_width = random.randint(200, 1000)
                new_width = new_width - new_width % 16 # Cut off to the nearest multiple of 16
                new_p = Platform(new_start, height, new_width, 16)
                platform_level.append(new_p)
                self.statics.add(new_p)
                rightmost = new_start + new_width
            while leftmost > min_left:
                new_start = leftmost - random.randint(150, 300)
                new_width = random.randint(200, 1000)
                new_width = new_width - new_width % 16 # Cut off to the nearest multiple of 16
                new_p = Platform(new_start - new_width, height, new_width, 16)
                platform_level.append(new_p)
                self.statics.add(new_p)
                leftmost = new_start - new_width
    
        # Generate platforms based on camera position: Make sure there are always platforms extending at least as far as +-4*game_constants.w, +-4*game_constants.h from the player
        max_height = self.camera.top - 2 * game_constants.h
        lowest = max(self.platforms.keys())
        highest = min(self.platforms.keys())
            
        for h in range(highest, lowest, 80):
            fill_level(h, self.camera)

        while highest > max_height:
            highest -= 80
            fill_level(highest, self.camera)
        
    def redraw(self): # Re-blit the background
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.header, (0, 0))

    def draw_header(self):
        dirty = []
        self.screen.set_clip(0, 0, game_constants.w, self.headersize) # Only draw in header area
        self.score.clear(self.screen, self.header)
        self.health.clear(self.screen, self.header)
        dirty += self.score.draw(self.screen, self.time_elapsed)
        dirty += self.health.draw(self.screen)
        return dirty

    def draw(self):
        self.camshift()
        
        header_dirty = self.draw_header()
        
        dirty = []
        self.screen.set_clip(0, self.headersize, game_constants.w, game_constants.h) # Don't draw over header
        # Clear phase
        self.screenstatics.clear(self.screen, self.background)
        self.powerups.clear(self.screen, self.background)
        self.actives.clear(self.screen, self.background)
        self.player.bullets.clear(self.screen, self.background)
        self.playergroup.clear(self.screen, self.background)
        
        # Draw phase
        dirty += self.screenstatics.draw(self.screen, self.camera)
        dirty += self.powerups.draw(self.screen, self.camera)
        dirty += self.actives.draw(self.screen, self.camera)
        dirty += self.playergroup.draw(self.screen, self.camera)
        dirty += self.player.bullets.draw(self.screen, self.camera)
        if self.player.selected_opponent: # cute little hack: repaint selected_opponent to make sure it's visible
            self.player.selected_opponent.draw(self.screen, self.camera)
        
        # Constrain all dirty rectangles in main game area to main game area.
        dirty = [dirty_rect.clip(self.screen.get_clip()) for dirty_rect in dirty]
        
        return header_dirty + dirty

    def camshift(self):
        newpos = self.player.rect
        bounds = self.camera.inflate(-game_constants.w + 50, -game_constants.h + 100)
        # Move the screen if we're near the edge
        if newpos.right > bounds.right:
            self.camera = self.camera.move(newpos.right - bounds.right, 0)
        elif newpos.left < bounds.left:
            self.camera = self.camera.move(newpos.left - bounds.left, 0)
        if newpos.bottom > bounds.bottom:
            self.camera = self.camera.move(0, newpos.bottom - bounds.bottom)
        elif newpos.top < bounds.top:
            self.camera = self.camera.move(0, newpos.top - bounds.top)
        self.screencheck()

    def screencheck(self): # Classify objects by whether they are on the screen
        for platform_level in self.platforms.values():
            for platform in platform_level:
                if platform not in self.screenstatics: # This platform wasn't on the screen: is it now?
                    if platform.rect.colliderect(self.camera):
                        self.screenstatics.add(platform)
                        # If it's a platform (has the attribute'word') give it an identifying word while it's onscreen
                        if hasattr(platform, 'word'):
                            platform.word = Word(self.special_chars.new(), Platform.font)
                else: # This platform is on the screen: is it gone now?
                    if not platform.rect.colliderect(self.camera):
                        self.screenstatics.remove(platform)
                        # If it's a platform (has the attribute'word') and it's out of camera, free up its symbol for later use
                        if hasattr(platform, 'word'):
                            self.special_chars.release(platform.word.string)
                            platform.word = None
        for sprite in self.powerups.sprites():
            if not sprite.rect.colliderect(self.camera.inflate(game_constants.w, 0)):
                sprite.kill()
        for sprite in self.actives.sprites(): # need a list because we're going to delete from it
            # Opponents are allowed to be a full screen width outside of camera, but no further
            if not sprite.rect.colliderect(self.camera.inflate(game_constants.w, 0)):
                if sprite == self.player.selected_opponent:
                    self.player.selected_opponent = None
                sprite.kill()

    def tick(self, elapsed):
        self.place_platforms()
    
        self.time_elapsed = elapsed
        for direction in self.movelist:
            self.player.direct(direction)
        for active_obj in self.actives:
            active_obj.tick(self.player.rect.center)
        for powerup in self.powerups:
            powerup.tick()
        for screenstatic in self.screenstatics: # Objects on the screen
            # Only platforms have a 'word' attribute
            if hasattr(screenstatic, 'word'):
                # Will it be possible to get to this object without having to walk on air
                screenstatic.reachable = is_reachable(screenstatic, self.player.rect, self.screenstatics)
        self.player.tick()

    def type_special(self, key): # Typing a special character
        for platform_level in self.platforms.values():
            for platform in platform_level:
                if hasattr(platform, 'word'): # HACK to ignore bottom platform
                    if platform.reachable and self.camera.colliderect(platform.rect):
                        if key == platform.contents():
                            return platform       
    def showMe(self):
        return self.health.value() != 0
        
    def exitChallenge(self):                            
        self.challenging = False
        self.screen.blit(self.background, (0, 0))
        
class ChallengeScreen:
    def __init__(self, screen, sentence):
        self.screen = screen
        self.font = pygame.font.Font('freesansbold.ttf', 40)
        self.challenge_message = self.font.render("TYPING CHALLENGE!", 0, Color.MOSTLY_WHITE)
        self.rect = None
        self.screen.fill((10, 10, 0))
        self.frames = 0

        pygame.draw.rect(screen, (100, 30, 200), (-10000, game_constants.h - 80, 20000, 10), 0)
        player = Player((0, 0))
        player.idleright.draw(screen, (game_constants.w / 8, game_constants.h - 80 - 38))
        from opponents import Commando
        commando = Commando("buttes", (0, 0))
        commando.idleleft.draw(screen, (game_constants.w * (7 / 8.0), game_constants.h - 80 - 35))

        sentence.draw(screen, (game_constants.w / 2, game_constants.h / 2))
        
        self.showing = True

    def showMe(self):
        return self.showing

    def draw(self):
        self.frames += 1
        
        if self.frames < 100:
            percent = self.frames / 100.0
            xpos = percent * game_constants.w / 2
        elif self.frames > 355:
            percent = (self.frames - 355) / 100.0
            xpos = game_constants.w / 2 + percent * game_constants.w / 2
        else:
            xpos = game_constants.w / 2

        message_rectangle = self.challenge_message.get_rect(centerx = xpos, centery = game_constants.h / 4)
            
        if 200 < self.frames < 455: # Transparent fadeout of text
            self.challenge_message.set_alpha(255 - (self.frames - 200))
        
        if self.rect:
            self.screen.fill((10, 10, 0), self.rect)
        self.screen.blit(self.challenge_message, message_rectangle)
        
        self.rect = message_rectangle
