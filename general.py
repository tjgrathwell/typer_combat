import pygame, os, random

class Color:
    """ A set of colors used in this game """
    word_unselect        = (200, 40, 200)
    word_select          = (250, 10, 30)
    platform_unreachable = (40, 40, 40)
    platform_reachable   = (230, 230, 230)
    platform_selected    = (230, 230, 0)
    text_normal          = (255, 255, 255)
    text_typed           = (50, 50, 50)
    score_color          = (200, 200, 100)

    WORD_BACKGROUND      = (40, 30, 200)

    BLACK_YELLOW         = (10, 10, 0)
    YELLOW               = (230, 230, 0)

    BLACK                = (0, 0, 0)
    DARK_GRAY            = (50, 50, 50)
    GRAY                 = (150, 150, 150)
    LIGHT_GRAY           = (200, 200, 200)
    MOSTLY_WHITE         = (250, 250, 250)
    WHITE                = (255, 255, 255)

class Options:
    selected_feeds     = ['Google', 'Slashdot', 'Digg']
    selected_opponents = ['Soldier', 'Copter', 'Ghost']

class game_constants:
    """ A set of constants used in this game, that should probably go elsewhere """
    speed             = 2.0
    bulletspeed       = 25
    terminal_velocity = -10
    jumpspeed         = 2.0
    jumpframes        = 45
    hitframes         = 10
    big_distance      = 9999999
    maxjump_height    = speed * jumpframes

    # Stupid hack. Calculate this per-class to calculate proper jumps.
    maxjump_width     = jumpspeed * jumpframes / 5
    max_enemies       = 10
    max_powerups      = 5
    w, h              = (800, 600)
    line_char_limit   = 40

Fonts = {}
def GetFont(pointSize):
    if Fonts.has_key(pointSize):
        return Fonts[pointSize]
    else:
        Fonts[pointSize] = pygame.font.Font('freesansbold.ttf', pointSize)
        return Fonts[pointSize]

class RenderUpdatesDraw(pygame.sprite.RenderClear):
    """ Call sprite.draw(surface, campos) for each sprite, keep track of dirty areas. """

    def draw(self, surface, campos):
        # "Dirty" will be a list of rects to send to pygame.display.update()
        dirty = self.lostsprites # Rects that have been deleted since last draw
        self.lostsprites = []

        for sprite, rect in self.spritedict.items():
            newrect = sprite.draw(surface, campos)

            if rect is 0:
                # This sprite wasn't onscreen last frame, draw over where the sprite was
                dirty.append(newrect)
            else:
                # Assumes that last and current rects will always overlap.
                # If not, faster to do a collide check first. See sprite.py.
                dirty.append(newrect.union(rect))

            self.spritedict[sprite] = newrect

        return dirty

def flippedframes(surfaces):
    return [pygame.transform.flip(image, True, False) for image in surfaces]

def loadframes(directory, filenames):
    return [pygame.image.load(os.path.join('.', 'data', directory, filename)).convert_alpha() for filename in filenames]

class WrappedSprite(pygame.sprite.Sprite):
    """ Wrapper around pygame.sprite.Sprite to consolidate methods specific to this game """

    def __init__(self):
        try:
            getattr(self, 'images_loaded')
        except AttributeError:
            self.loadImages()

        super(WrappedSprite, self).__init__()

    @classmethod
    def loadImages(cls):
        cls.images = {}
        cls.images_loaded = True

class Anim(WrappedSprite):
    """ Collection of frames meant to be displayed sequentially through time """

    def __init__(self, images, framecounts, delay = 0, ends = False, offset = (0, 0)):
        super(Anim, self).__init__()

        self.offset = offset
        self.ends = ends
        self.delay = delay

        self.total_frames = len(images)
        self.framecounts = framecounts

        self.images = images
        self.reset() # Reset current frame

    def reset(self):
        self.frames = 0
        self.current_frame = 0

    def clone(self, newdelay = 0, newoffset = (0, 0)):
        return Anim(self.images, self.framecounts, delay = newdelay, ends = self.ends, offset = newoffset)

    def get_rect(self):
        width, height = 0, 0
        for image in self.images:
            if image.get_width() > width:
                width = image.get_width()
            if image.get_height() > height:
                height = image.get_height()
        return pygame.rect.Rect(0, 0, width, height)

    def draw(self, surface, position):
        if self.delay:
            return pygame.rect.Rect((position.topleft), (0, 0))
        else:
            return surface.blit(self.images[self.current_frame], (position[0] + self.offset[0], position[1] + self.offset[1]))

    def tick(self):
        if self.delay:
            self.delay -= 1
            return
        self.frames += 1

        if self.frames % self.framecounts[self.current_frame] == 0:
            if self.ends and self.images[self.current_frame] == self.images[-1]: # Stop animation on last frame
                self.kill()
            else:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                self.image = self.images[self.current_frame]
                self.frames = 0

    def total_time(self):
        return sum(self.framecounts) + self.delay

class Box(WrappedSprite):
    """ A boundary rect that can draw itself to the screen when given a camera position """

    def __init__(self, x, y, w, h):
        super(Box, self).__init__()
        self.rect = pygame.rect.Rect((x, y, w, h))

    @classmethod
    def loadImages(cls):
        super(Box, cls).loadImages()
        cls.images['smbas']      = loadframes('platforms', ('smbas.png',))[0]
        cls.images['smbas_edge'] = loadframes('platforms', ('smbas_edge.png',))[0]

    def draw(self, surface, campos):
        moved = self.rect.move(-campos[0], -campos[1])
        w = moved.width
        for i in xrange(w / 16):
            if i == 0 or i == (w / 16 - 1):
                surface.blit(self.images['smbas_edge'], (moved.left + i * 16, moved.top))
            else:
                surface.blit(self.images['smbas'], (moved.left + i * 16, moved.top))
        return moved

class Score(pygame.sprite.Sprite):
    """ Displays score in the upper-right of screen. Draw function requires total elapsed time since game start. """

    def __init__(self, surface, color = Color.score_color):
        super(Score, self).__init__()

        self.font = GetFont(14)
        self.color = color
        self.score = 0.0
        self.misses = 0
        self.frames = 0
        self.render_initial(surface)
        self.drawscore, self.drawmiss, self.drawwpm = (True, True, True)

        self.drawn_once = False

    def render_initial(self, surface):
        self.rendered_score =  self.font.render("Score: %.2f" % self.score,  1, self.color)
        self.rendered_misses = self.font.render("Misses: %i"  % self.misses, 1, self.color)
        self.rendered_wpm =    self.font.render("WPM: %3i"    % 0,           1, self.color)

        left_edge = surface.get_rect().right - self.rendered_wpm.get_rect().width * 1.5
        self.wpm_rect = self.rendered_wpm.get_rect(top = 5, left = left_edge)
        left_edge -= self.rendered_misses.get_rect().width * 1.5
        self.miss_rect = self.rendered_misses.get_rect(top = 5, left = left_edge)
        left_edge -= self.rendered_score.get_rect().width * 1.5
        self.score_rect = self.rendered_score.get_rect(top = 5, left = left_edge)

    def increase(self, value):
        self.score += value
        self.rendered_score = self.font.render("Score: %.2f" % self.score, 1, self.color)
        self.drawscore = True

    def miss(self):
        self.misses += 1
        self.rendered_misses = self.font.render("Misses: %i" % self.misses, 1, self.color)
        self.drawmiss = True

    def clear(self, surface, background):
        if not self.drawn_once: return

        if self.drawscore:
            surface.blit(background, self.score_rect)
        if self.drawmiss:
            surface.blit(background, self.miss_rect)
        if self.drawwpm:
            surface.blit(background, self.wpm_rect)

    def draw(self, surface, elapsed):
        self.frames += 1

        if self.frames > 60: # Choose whether to draw wpm next frame
            self.rendered_wpm = self.font.render("WPM: %3i" % (self.score / (elapsed / 60)), 1, self.color)
            self.drawwpm = True
            self.frames = 0

        dirty = []
        if self.drawwpm:
            dirty += [surface.blit(self.rendered_wpm, self.wpm_rect)]
            self.drawwpm = True

        if self.drawmiss:
            dirty += [surface.blit(self.rendered_misses, self.miss_rect)]
            self.drawmiss = True

        if self.drawscore:
            dirty += [surface.blit(self.rendered_score, self.score_rect)]
            self.drawscore = True

        self.drawn_once = True

        return dirty

# WordMaker:
# this could possibly be folded into Word, or extended to keep better track of what
# words are in play.
class WordMaker:
    """ Holds an array of words and selects one through random.choice()
        Could possibly be extended to track active words rather than
        relying on other classes to ensure two similar words don't get spawned.
    """

    def __init__(self, words):
        self.word_array = words

    def next_word(self, not_starting_with = None):
        while True:
            new_word = Word(random.choice(self.word_array))
            if (not_starting_with and (new_word.string[0] in not_starting_with)):
                continue
            return new_word

class Word(pygame.sprite.Sprite):
    """ A string that keeps track of how much of it has been completed,
          as well as its current rendered image.
        A word can be drawn to the screen or 'typed on'
    """

    def __init__(self, text, font = None):
        super(Word, self).__init__()

        self.font = font or GetFont(24)
        self.borderwidth = self.font.get_height() / 5

        self.string = text
        self.rect = None
        self.reset()

    def split_sentence(self, sentence, offset = 0):
        def str_len_line(line):
            return sum([len(x) for x in line])

        result = []
        line = []
        splitwords = sentence.split(" ")
        for word in splitwords:
            if (str_len_line(line) + len(word)) > game_constants.line_char_limit:
                result.append(" ".join(line))
                line = []
            elif (str_len_line(line) + len(word) + offset) > game_constants.line_char_limit:
                offset = 0
                result.append(" ".join(line))
                line = []
            line.append(word)
        if line:
            result.append(" ".join(line))
        return result

    def reset(self):
        self.strpos = 0
        self.ltext = []
        right_side_string = self.split_sentence(self.string)
        self.rtext = [self.font.render(line, 1, Color.text_normal) for line in right_side_string]

    def _rerender_sentence(self):
        if self.strpos > 0:
            left_side_string = self.split_sentence(self.string[:self.strpos])
            self.ltext = [self.font.render(line, 1, Color.text_typed) for line in left_side_string]
            right_side_string = self.split_sentence(self.string[self.strpos:], len(left_side_string[-1]))
        else:
            right_side_string = self.split_sentence(self.string)
            self.rtext = [self.font.render(line, 1, Color.text_normal) for line in right_side_string]

    def rerender(self):
        if len(self.string) < game_constants.line_char_limit:
            self.ltext = [self.font.render(self.string[:self.strpos], 1, Color.text_typed)]
            self.rtext = [self.font.render(self.string[self.strpos:], 1, Color.text_normal)]
        else:
            self._rerender_sentence()

    def draw(self, surface, (x, y), border_color = Color.word_unselect):
        if self.ltext:
            ltext_rects = [self.ltext[0].get_rect(centerx = x, centery = y)]
        else:
            ltext_rects = []
        for i, line in enumerate(self.ltext[1:]):
            ltext_rects.append(line.get_rect(centerx = x, centery = y + self.ltext_rects[i].height))
        if self.ltext:
            rtext_rects = [self.rtext[0].get_rect(left = ltext_rects[-1].right, centery = ltext_rects[-1].centery)]
        else:
            rtext_rects = [self.rtext[0].get_rect(centerx = x, centery = y)]
        for i, line in enumerate(self.rtext[1:]):
            rtext_rects.append(line.get_rect(centerx = x, top = rtext_rects[i].bottom))

        # Perform correction on edge
        if ltext_rects and rtext_rects:
            w = ltext_rects[-1].width + rtext_rects[0].width
            ltext_rects[-1].left = x - w / 2
            rtext_rects[0].right = x + w / 2

        allrects = ltext_rects + rtext_rects

        rect_inflation = (8 + self.borderwidth, 5 + self.borderwidth)
        if len(allrects) == 1:
            self.rect = allrects[0].inflate(rect_inflation)
        else:
            self.rect = allrects[0].unionall(allrects[1:]).inflate(rect_inflation)

        surface.fill(Color.WORD_BACKGROUND, self.rect)
        screen_rect = pygame.draw.rect(surface, border_color, self.rect, self.borderwidth)

        for line, rect in zip(self.ltext, ltext_rects):
            surface.blit(line, rect)
        for line, rect in zip(self.rtext, rtext_rects):
            surface.blit(line, rect)

        # HACK? or bug in pygame (i assume I meant the +1...)
        return screen_rect.inflate(self.borderwidth + 1, self.borderwidth + 1)

    def typeon(self, char):
        if char == self.string[self.strpos]:
            self.strpos += 1
            self.rerender()
            return True
        return False

    def done(self):
        return self.strpos == len(self.string)

def n_of(format_string, n):
    return [format_string % i for i in xrange(1, n + 1)]
