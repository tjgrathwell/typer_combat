import pygame, os, random

class Color:
    """ A set of colors used in this game """
    word_unselect = (200, 40, 200)
    word_select = (250, 10, 30)
    platform_unreachable = (40, 40, 40)
    platform_reachable = (230, 230, 230)
    platform_selected = (230, 230, 0)
    text_normal = (255, 255, 255)
    text_typed = (50, 50, 50)
    score_color = (200, 200, 100)

    YELLOW = (230, 230, 0)

    BLACK = (0, 0, 0)
    DARK_GRAY = (50, 50, 50)
    GRAY = (150, 150, 150)
    LIGHT_GRAY = (200, 200, 200)
    MOSTLY_WHITE = (250, 250, 250)
    WHITE = (255, 255, 255)

class game_constants:
    """ A set of constants used in this game, that should probably go elsewhere """
    speed = 2.0
    bulletspeed = 25
    terminal_velocity = -10
    jumpspeed = 2.0
    jumpframes = 45
    hitframes = 10
    big_distance = 9999999
    maxjump_height = speed * jumpframes
    maxjump_width = jumpspeed * jumpframes / 5 # Super temporary stupid hack. Calculate this per-class to calculate proper jumps.
    max_enemies = 10
    max_powerups = 5
    w, h = (800, 600)
    line_char_limit = 40
    
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
        for s, r in self.spritedict.items(): # sprite, rectangle for all sprites still active
            newrect = s.draw(surface, campos) # Use the sprite's draw function, which should return a rect
            if r is 0: # This sprite wasn't onscreen last frame
                dirty.append(newrect) # Need to draw over where the sprite was
            else:
                dirty.append(newrect.union(r)) # Assumes that last and current rects will always overlap. If not, faster to do a collide check first. See sprite.py.
            self.spritedict[s] = newrect
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
        cls.images_smbas = loadframes('platforms', ('smbas.png',))[0]
        cls.images_smbas_edge = loadframes('platforms', ('smbas_edge.png',))[0]
        
    def draw(self, surface, campos):
        moved = self.rect.move(-campos[0], -campos[1])
        w = moved.width
        for i in xrange(w / 16):
            if i == 0 or i == (w / 16 - 1):
                surface.blit(Box.images_smbas_edge, (moved.left + i * 16, moved.top))
            else:
                surface.blit(Box.images_smbas, (moved.left + i * 16, moved.top))
        return moved
        
class Circle(pygame.sprite.Sprite):
    """ A drawable circle that purports to store its boundary rect, but doesn't because I can't figure it out. """

    def __init__(self, center, radius):
        super(Circle, self).__init__()
        self.rect = pygame.rect.Rect(0, 0, radius, radius)
        self.rect.center = center
        self.center = center
        self.radius = radius

    def draw(self, surface, (x, y)):
        moved = (self.center[0] - x, self.center[1] - y)
        pygame.draw.circle(surface, (100, 30, 200), moved, 12)
        
class Platform(Box):
    """ A Box with a bunch of collision rules used in the game """

    font = None
    def __init__(self, x, y, w, h):
        Box.__init__(self, x, y, w, h)
        self.word = None
        self.reachable = False
        self.selected = False

    def draw(self, surface, campos):
        box = Box.draw(self, surface, campos)
        # It feels like maybe this label code should go elsewhere
        if self.word:
            if self.selected: color = Color.platform_selected
            elif self.reachable: color = Color.platform_reachable
            else: color = Color.platform_unreachable
            left = self.word.draw(surface, (self.rect.left - campos[0] + 10, self.rect[1] - campos[1] + 5), color)
            right = self.word.draw(surface, (self.rect.right - campos[0] - 10, self.rect[1] - campos[1] + 5), color)
        return box.union(left.union(right)) # HACK

    def contents(self):
        return self.word.string

    def setword(self, text):
        if not self.word: self.word = Word(text, Platform.font)
             
class SpecialChars:
    """ Keeps track of what ASCII special keys are in use by current platforms, so that dupilicate keys are not used. """

    def __init__(self):
        self.keys = "1234567890[]\;',./!@#$%^&*(){}|:\"<>?"
        self.inuse = []

    def new(self):
        if len(self.inuse) == len(self.keys): return False
        while True:
            key = random.choice(self.keys)
            if key not in self.inuse:
                self.inuse.append(key)
                return key

    def release(self, char):
        self.inuse.remove(char)
          
class Score(pygame.sprite.Sprite):
    """ Displays score in the upper-right of screen. Draw function requires total elapsed time since game start. """

    font = None
    def __init__(self, surface, color = Color.score_color):
        super(Score, self).__init__()
        self.color = color
        self.score = 0.0
        self.misses = 0
        self.frames = 0
        self.render_initial(surface)
        self.drawscore, self.drawmiss, self.drawwpm = (True, True, True)

        self.drawn_once = False

    def render_initial(self, surface):
        self.rendered_score =  Score.font.render("Score: %.2f" % self.score,  1, self.color)
        self.rendered_misses = Score.font.render("Misses: %i"  % self.misses, 1, self.color)
        self.rendered_wpm =    Score.font.render("WPM: %3i"    % 0,           1, self.color)

        left_edge = surface.get_rect().right - self.rendered_wpm.get_rect().width * 1.5
        self.wpm_rect = self.rendered_wpm.get_rect(top = 5, left = left_edge)
        left_edge -= self.rendered_misses.get_rect().width * 1.5
        self.miss_rect = self.rendered_misses.get_rect(top = 5, left = left_edge)
        left_edge -= self.rendered_score.get_rect().width * 1.5
        self.score_rect = self.rendered_score.get_rect(top = 5, left = left_edge)

    def increase(self, value):
        self.score += value
        self.rendered_score = Score.font.render("Score: %.2f" % self.score, 1, self.color)
        self.drawscore = True

    def miss(self):
        self.misses += 1
        self.rendered_misses = Score.font.render("Misses: %i" % self.misses, 1, self.color)
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
            self.rendered_wpm = Score.font.render("WPM: %3i" % (self.score / (elapsed / 60)), 1, self.color)
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

    def next_word(self):
        return Word(random.choice(self.word_array))
            
def split_sentence(sentence, offset = 0):
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
            
class Word(pygame.sprite.Sprite):
    """ A string that keeps track of how much of it has been completed, as well as its current rendered image
        A word can be drawn to the screen or 'typed on'
    """

    font = None
    def __init__(self, text, font = None):
        super(Word, self).__init__()

        if not font: font = self.font
        self.font = font
        self.borderwidth = font.get_height() / 5

        self.string = text
        self.rect = None
        self.lastrect = pygame.rect.Rect(0, 0, 0, 0)
        self.reset()

    def reset(self):
        self.strpos = 0
        self.ltext = []
        right_side_string = split_sentence(self.string)
        self.rtext = [self.font.render(line, 1, Color.text_normal) for line in right_side_string]

    def rerender(self):
        if self.string < game_constants.line_char_limit:
            self.ltext = [self.font.render(self.string[:self.strpos], 1, Color.text_typed)]
            self.rtext = [self.font.render(self.string[self.strpos:], 1, Color.text_normal)]
        else:
            if self.strpos > 0:
                left_side_string = split_sentence(self.string[:self.strpos])
                self.ltext = [self.font.render(line, 1, Color.text_typed) for line in left_side_string]
                right_side_string = split_sentence(self.string[self.strpos:], len(left_side_string[-1]))
            else:
                right_side_string = split_sentence(self.string)
            self.rtext = [self.font.render(line, 1, Color.text_normal) for line in right_side_string]

    def draw(self, surface, (x, y), border_color = Color.word_unselect):
        if self.ltext:
            ltext_rects = [self.ltext[0].get_rect(centerx = x, centery = y)]
        else:
            ltext_rects = []
        for i, line in enumerate(self.ltext[1:]):
            ltext_rects.append(line.get_rect(centerx = x, centery = y+self.ltext_rects[i].height))
        if self.ltext:
            rtext_rects = [self.rtext[0].get_rect(left = ltext_rects[-1].right, centery = ltext_rects[-1].centery)]
        else:
            rtext_rects = [self.rtext[0].get_rect(centerx = x, centery = y)]
        for i, line in enumerate(self.rtext[1:]):
            rtext_rects.append(line.get_rect(centerx = x, top = rtext_rects[i].bottom))

        if ltext_rects and rtext_rects: # Perform correction  on edge
            w = ltext_rects[-1].width + rtext_rects[0].width
            ltext_rects[-1].left = x - w / 2
            rtext_rects[0].right = x + w / 2
            
        allrects = ltext_rects + rtext_rects
        if len(allrects) == 1:
            self.rect = allrects[0].inflate(8, 3)
        else:
            self.rect = allrects[0].unionall(allrects[1:]).inflate(8, 3)

        surface.fill((40, 30, 200), self.rect)
        screen_rect = pygame.draw.rect(surface, border_color, self.rect, self.borderwidth)

        for line, rect in zip(self.ltext, ltext_rects):
            surface.blit(line, rect)
        for line, rect in zip(self.rtext, rtext_rects):
            surface.blit(line, rect)

        self.lastrect = screen_rect
        return screen_rect.inflate(self.borderwidth + 1, self.borderwidth + 1) # HACK? or bug in pygame

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
    
def loadImagesForAnimations():
    """ Load all the images in the game from files into surfaces as class members. """
    from opponents import Assorted
    
    [cls.loadImages() for cls in [Assorted]]
