import pygame, os, random, math

class Color:
    """ A set of colors used in this game """
    word_unselect = (200, 40, 200)
    word_select = (250, 10, 30)
    platform_unreachable = (40, 40, 40)
    platform_reachable = (230, 230, 230)
    platform_selected = (230,230,0)
    text_normal = (255,255,255)
    text_typed = (50,50,50)
    score_color = (200, 200, 100)

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
    w, h = (800,600)
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
    return [pygame.transform.flip(image,True,False) for image in surfaces]
    
def loadframes(directory,filenames):
    return [pygame.image.load(os.path.join('.','data',directory,filename)).convert_alpha() for filename in filenames]
    
class Anim(pygame.sprite.Sprite):
    """ Collection of frames meant to be displayed sequentially through time """
    def __init__(self,images,framecounts, delay=0, ends=False, offset=(0,0)):
        pygame.sprite.Sprite.__init__(self)
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
    def clone(self,newdelay=0,newoffset=(0,0)):
        return Anim(self.images,self.framecounts,delay=newdelay,ends=self.ends,offset=newoffset)
    def get_rect(self):
        width, height = 0,0
        for image in self.images:
            if image.get_width() > width:
                width = image.get_width()
            if image.get_height() > height:
                height = image.get_height()
        return pygame.rect.Rect(0,0,width,height)
    def draw(self,surface,position):
        if self.delay:
            return pygame.rect.Rect((position.topleft),(0,0))
        else:
            return surface.blit(self.images[self.current_frame], (position[0]+self.offset[0],position[1]+self.offset[1]))
    def tick(self):
        if self.delay:
            self.delay -= 1
            return
        self.frames += 1
         
        if self.frames % self.framecounts[self.current_frame] == 0:
            if self.ends and self.images[self.current_frame] == self.images[-1]: # Stop animation on last frame
                self.kill()
            else:
                self.current_frame = (self.current_frame+1) % self.total_frames
                self.image = self.images[self.current_frame]
                self.frames = 0
    def total_time(self):
        return sum(self.framecounts) + self.delay
            
class Box(pygame.sprite.Sprite):
    """ A boundary rect that can draw itself to the screen when given a camera position """
    def __init__(self,x,y,w,h):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.rect.Rect((x,y,w,h))
    def draw(self,surface,campos):
        moved = self.rect.move(-campos[0], -campos[1])
        w = moved.width
        for i in xrange(w/16):
            if i == 0 or i == (w/16 - 1):
                surface.blit(Box.images_smbas_edge, (moved.left + i*16, moved.top))
            else:
                surface.blit(Box.images_smbas, (moved.left + i*16, moved.top))
        return moved
        
class Circle(pygame.sprite.Sprite):
    """ A drawable circle that purports to store its boundary rect, but doesn't because I can't figure it out. """
    def __init__(self,center,radius):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.rect.Rect(0,0,radius,radius)
        self.rect.center = center
        self.center = center
        self.radius = radius
    def draw(self,surface,(x,y)):
        moved = (self.center[0]-x,self.center[1]-y)
        pygame.draw.circle(surface, (100, 30, 200), moved, 12)
        
class Platform(Box):
    """ A Box with a bunch of collision rules used in the game """
    font = None
    def __init__(self,x,y,w,h):
        Box.__init__(self,x,y,w,h)
        self.word = None
        self.reachable = False
        self.selected = False
    def draw(self,surface,campos):
        box = Box.draw(self,surface,campos)
        # It feels like maybe this label code should go elsewhere
        if self.word:
            if self.selected: color = Color.platform_selected
            elif self.reachable: color = Color.platform_reachable
            else: color = Color.platform_unreachable
            left = self.word.draw(surface,(self.rect.left-campos[0]+10,self.rect[1]-campos[1]+5),color)
            right = self.word.draw(surface,(self.rect.right-campos[0]-10,self.rect[1]-campos[1]+5),color)
        return box.union(left.union(right)) # HACK
    def contents(self):
        return self.word.string
    def setword(self,text):
        if not self.word: self.word = Word(text,Platform.font)
             
class SpecialChars:
    """ Keeps track of what ASCII special keys are in use by current platforms, so that dupilicate keys are not used. """
    def __init__(self):
        self.keys = "1234567890[]\;',./!@#$%^&*(){}|:\"<>?"
        self.inuse = []
    def new(self):
        if len(self.inuse) == len(self.keys): return False
        while True:
            next = random.choice(self.keys)
            if next not in self.inuse:
                self.inuse.append(next)
                return next
    def release(self, char):
        self.inuse.remove(char)
          
class Score(pygame.sprite.Sprite):
    """ Displays score in the upper-right of screen. Draw function requires total elapsed time since game start. """
    font = None
    def __init__(self,surface,color=Color.score_color):
        pygame.sprite.Sprite.__init__(self)
        self.color = color
        self.score = 0.0
        self.misses = 0
        self.frames = 0
        self.render_initial(surface)
        self.drawscore, self.drawmiss, self.drawwpm = (True, True, True)

        self.drawn_once = False
    def render_initial(self,surface):
        self.rendered_score =  Score.font.render("Score: %.2f" % self.score,  1, self.color)
        self.rendered_misses = Score.font.render("Misses: %i"  % self.misses, 1, self.color)
        self.rendered_wpm =    Score.font.render("WPM: %3i"    % 0,           1, self.color)

        left_edge = surface.get_rect().right - self.rendered_wpm.get_rect().width * 1.5
        self.wpm_rect = self.rendered_wpm.get_rect(top=5, left=left_edge)
        left_edge -= self.rendered_misses.get_rect().width * 1.5
        self.miss_rect = self.rendered_misses.get_rect(top=5, left=left_edge)
        left_edge -= self.rendered_score.get_rect().width * 1.5
        self.score_rect = self.rendered_score.get_rect(top=5, left=left_edge)
    def increase(self,value):
        self.score += value
        self.rendered_score = Score.font.render("Score: %.2f" % self.score, 1, self.color)
        self.drawscore = True
    def miss(self):
        self.misses += 1
        self.rendered_misses = Score.font.render("Misses: %i" % self.misses, 1, self.color)
        self.drawmiss = True
    def clear(self,surface,background):
        if not self.drawn_once: return
        
        if self.drawscore:
            surface.blit(background, self.score_rect)
        if self.drawmiss:
            surface.blit(background, self.miss_rect)
        if self.drawwpm:
            surface.blit(background, self.wpm_rect)
    def draw(self,surface,elapsed):
        self.frames += 1
       
        if self.frames > 60: # Choose whether to draw wpm next frame
            self.rendered_wpm = Score.font.render("WPM: %3i" % (self.score/(elapsed/60)), 1, self.color)
            self.drawwpm = True
            self.frames = 0        
        
        dirty = []
        if self.drawwpm:
            dirty += [surface.blit(self.rendered_wpm,self.wpm_rect)]
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
    def __init__(self,words):
        self.word_array = words
    def next(self):
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
    def __init__(self,text,font=None):
        if not font: font = self.font
        self.font = font
        self.borderwidth = font.get_height()/5
        pygame.sprite.Sprite.__init__(self)
        self.string = text
        self.rect = None
        self.lastrect = pygame.rect.Rect(0,0,0,0)
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
    def draw(self,surface,(x,y),border_color=Color.word_unselect):
        if self.ltext:
            ltext_rects = [self.ltext[0].get_rect(centerx=x, centery=y)]
        else:
            ltext_rects = []
        for i,line in enumerate(self.ltext[1:]):
            ltext_rects.append(line.get_rect(centerx=x, centery=y+self.ltext_rects[i].height))
        if self.ltext:
            rtext_rects = [self.rtext[0].get_rect(left=ltext_rects[-1].right, centery=ltext_rects[-1].centery)]
        else:
            rtext_rects = [self.rtext[0].get_rect(centerx=x, centery=y)]
        for i,line in enumerate(self.rtext[1:]):
            rtext_rects.append(line.get_rect(centerx=x, top=rtext_rects[i].bottom))

        if ltext_rects and rtext_rects: # Perform correction  on edge
            w = ltext_rects[-1].width + rtext_rects[0].width
            ltext_rects[-1].left = x - w/2
            rtext_rects[0].right = x + w/2
            
        allrects = ltext_rects + rtext_rects
        if len(allrects) == 1:
            self.rect = allrects[0].inflate(8,3)
        else:
            self.rect = allrects[0].unionall(allrects[1:]).inflate(8,3)

        surface.fill((40,30,200), self.rect)
        screen_rect = pygame.draw.rect(surface, border_color, self.rect, self.borderwidth)

        for line,rect in zip(self.ltext,ltext_rects):
            surface.blit(line, rect)
        for line,rect in zip(self.rtext,rtext_rects):
            surface.blit(line, rect)

        self.lastrect = screen_rect
        return screen_rect.inflate(self.borderwidth+1,self.borderwidth+1) # HACK? or bug in pygame
    def typeon(self,char):
        if char == self.string[self.strpos]:
            self.strpos += 1
            self.rerender()
            return True
        return False
    def done(self):
        return self.strpos == len(self.string)
 
def n_of(format_string, n):
    return [format_string % i for i in xrange(1,n+1)] 
    
def loadImagesForAnimations():
    """ Load all the images in the game from files into surfaces as class members. """
    # I really hate doing it like this, but I can't initialize them with classes because pygame isn't initialized at class initialization time. The only other option would
    # be to set, say, Player.images_upright to ("gunstar",("gunup1.png","gunup2.png")) in Player's actual code, and have this function go through ALL classes with
    # images and re-save every Class.images_* member as the loaded series of surfaces. I'll get around to it eventually.
    from player import Player
    from opponents import Soldier, Copter, Ghost, Commando, Assorted
    from powerup import Heart, Shotgun
    
    Player.images_upright = loadframes("gunstar",("gunup1.png","gunup2.png"))
    Player.images_upleft = flippedframes(Player.images_upright)
    Player.images_upsideright = loadframes("gunstar",("gunupside1.png","gunupside2.png"))
    Player.images_upsideleft = flippedframes(Player.images_upsideright)
    Player.images_sideright = loadframes("gunstar",("gunside1.png","gunside2.png"))
    Player.images_sideleft = flippedframes(Player.images_sideright)
    Player.images_downsideright = loadframes("gunstar",("gundownside1.png","gundownside2.png"))
    Player.images_downsideleft = flippedframes(Player.images_downsideright)
    Player.images_downright = loadframes("gunstar",("gundown1.png","gundown2.png"))
    Player.images_downleft = flippedframes(Player.images_downright)
    Player.images_idleright = loadframes("gunstar",("rest1.png","rest2.png"))
    Player.images_idleleft = flippedframes(Player.images_idleright)
    Player.images_runright = loadframes("gunstar",n_of("run%i.png",6))
    Player.images_runleft = flippedframes(Player.images_runright)
    Player.images_jumpright = loadframes("gunstar",("jump1.png","jump2.png"))
    Player.images_jumpleft = flippedframes(Player.images_jumpright)
    Player.images_fallright = loadframes("gunstar",(["jump3.png"]))
    Player.images_fallleft = flippedframes(Player.images_fallright)
    Player.images_hitright = loadframes("gunstar",("hit1.png","hit2.png"))
    Player.images_hitleft = flippedframes(Player.images_hitright)

    Ghost.images_left = loadframes("ghost",("left1.gif","left2.gif"))
    Ghost.images_right = loadframes("ghost",("right1.gif","right2.gif"))
    Ghost.images_up = loadframes("ghost",("up1.gif","up2.gif"))
    Ghost.images_down = loadframes("ghost",("down1.gif","down2.gif"))
    
    Ghost.images_blue = loadframes("ghost",("blue1.gif","blue2.gif"))
    
    Ghost.images_eyesright = loadframes("ghost",(["eyesright.gif"]))
    Ghost.images_eyesleft = loadframes("ghost",(["eyesleft.gif"]))
    Ghost.images_eyesup = loadframes("ghost",(["eyesup.gif"]))
    Ghost.images_eyesdown = loadframes("ghost",(["eyesdown.gif"]))
    
    Soldier.images_idleright = loadframes("soldier",("rest1.gif","rest2.gif"))
    Soldier.images_idleleft = flippedframes(Soldier.images_idleright)
    Soldier.images_runright = loadframes("soldier",n_of("run%i.gif",4))
    Soldier.images_runleft = flippedframes(Soldier.images_runright)
    Soldier.images_fallright = loadframes("soldier",("fall1.gif","fall2.gif"))
    Soldier.images_fallleft = flippedframes(Soldier.images_fallright)
    Soldier.images_jumpright = loadframes("soldier",("flip1.gif","flip2.gif"))
    Soldier.images_jumpleft = flippedframes(Soldier.images_jumpright)
    
    Copter.images_fly = loadframes("copter",["fly%s.gif" % i for i in xrange(1,7)])
    
    Commando.images_idleright = loadframes("commando",("rest1.gif","rest2.gif"))
    Commando.images_idleleft = flippedframes(Commando.images_idleright)
    
    Assorted.images_explosion = loadframes("assorted",n_of("explosion%02.f.gif", 10))                        
    Assorted.images_heartfull = loadframes("assorted",(["heartfull.gif"]))
    Assorted.images_heartempty = loadframes("assorted",(["heartempty.gif"]))
    
    Heart.images_heart = loadframes("assorted",("heart1.gif","heart2.gif","heart3.gif","heart4.gif","heart5.gif",
                              "heart4.gif","heart3.gif","heart2.gif"))
                              
    Shotgun.images_shotgun = loadframes("assorted",(["shotgun1.gif"]))
    
    Box.images_smbas = pygame.image.load(os.path.join('.','data',"platforms","smbas.png")).convert_alpha()
    Box.images_smbas_edge = pygame.image.load(os.path.join('.','data',"platforms","smbas_edge.png")).convert_alpha()