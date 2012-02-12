import pygame, random, math
from general import RenderUpdatesDraw, game_constants, Color, Anim, loadframes, flippedframes, n_of, WrappedSprite
from player import Weapons, States
from collision import distfromground, clearshot

def rand_offset(value):
    return (random.randint(-value, value), random.randint(-value, value))

def getOpponent(name):
    if name == 'Soldier':
        return Soldier
    elif name == 'Copter':
        return Copter
    elif name == 'Ghost':
        return Ghost
    elif name == 'Commando':
        return Commando
    
class Opponent(WrappedSprite):
    """ A holder of a word, along with the game logic for moving around the screen and such. """

    name = "Nothing"
    def __init__(self, word, (x, y), statics, speed = 2.0):
        super(Opponent, self).__init__()
        self.statics = statics
        self.word = word
        self.typing = False
        self.speed = speed
        self.pause = 0
        (self.x, self.y) = (float(x), float(y))
        self.rect = pygame.rect.Rect(0, 0, 5, 5)
        self.rect.center = (self.x, self.y) # Smaller rect used for collision, NOT DRAWING
        self.ttl = None # Time to live when killed

    def draw(self, surface, camera):
        drawx, drawy = self.x - camera[0], self.y - camera[1]
        if self.typing:
            color = Color.word_select
        else:
            color = Color.word_unselect

        wordrect = self.word.draw(surface, (drawx, drawy - 10), color)
        opprect = pygame.draw.circle(surface, (200, 200, 200), (int(drawx), int(drawy)), 3).inflate(3, 3)
        return wordrect.union(opprect)

    def hit(self, weapon, shooter):
        if weapon == Weapons.normal:
            self.pause = 20
        elif weapon == Weapons.shotgun:
            self.pause = 40

    def typeon(self, char):
        if not self.word.done():
            if char == self.word.string[0]:
                self.typing = True
            success = self.word.typeon(char)
            return success

    def value(self):
        return len(self.word.string) / 5.0

    def move(self, (xt, yt)):
        if self.pause:
            self.pause -= 1
        else:
            xdist = xt - self.x
            ydist = yt - self.y
            dist = math.sqrt(xdist * xdist + ydist * ydist)
            nxdist, nydist = abs(xdist / dist), abs(ydist / dist)
            if not -2 < xdist < 2:
                if xdist < 0:
                    self.x -= nxdist * self.speed
                else:
                    self.x += nxdist * self.speed
            if not -2 < ydist < 2:
                if ydist < 0:
                    self.y -= nydist * self.speed
                else:
                    self.y += nydist * self.speed
        self.rect.center = (self.x, self.y)

    def defeated(self):
        return self.word.done()

    def release(self):
        self.typing = False
        self.word.reset()

    def tick(self, (xt, yt)):
        self.move((xt, yt))

    def destroy(self):
        self.kill() # remove self from all sprite lists
       
class Ghost(Opponent):
    """ A ghost can float through walls and will move on a direct line toward the player. """

    name = "Ghost"
    def __init__(self, word, (x, y), statics, speed = 2.2):
        super(Ghost, self).__init__(word, (x, y), statics, speed)
        self.loadanims()
        self.current_anim = self.anims['left']
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)
        
    @classmethod
    def loadImages(cls):
        super(Ghost, cls).loadImages()

        cls.images['left']      = loadframes("ghost", ("left1.gif", "left2.gif"))
        cls.images['right']     = loadframes("ghost", ("right1.gif", "right2.gif"))
        cls.images['up']        = loadframes("ghost", ("up1.gif", "up2.gif"))
        cls.images['down']      = loadframes("ghost", ("down1.gif", "down2.gif"))
        
        cls.images['blue']      = loadframes("ghost", ("blue1.gif", "blue2.gif"))
        
        cls.images['eyesright'] = loadframes("ghost", ("eyesright.gif",))
        cls.images['eyesleft']  = loadframes("ghost", ("eyesleft.gif",))
        cls.images['eyesup']    = loadframes("ghost", ("eyesup.gif",))
        cls.images['eyesdown']  = loadframes("ghost", ("eyesdown.gif",))

    def loadanims(self):
        self.anims = {}
        self.anims['left']      = Anim(self.images['left'],      (10, 10))
        self.anims['right']     = Anim(self.images['right'],     (10, 10))
        self.anims['up']        = Anim(self.images['up'],        (10, 10))
        self.anims['down']      = Anim(self.images['down'],      (10, 10))
        
        self.anims['blue']      = Anim(self.images['blue'],      (10, 10))
        
        self.anims['eyesright'] = Anim(self.images['eyesright'], (100,))
        self.anims['eyesleft']  = Anim(self.images['eyesleft'],  (100,))
        self.anims['eyesup']    = Anim(self.images['eyesup'],    (100,))
        self.anims['eyesdown']  = Anim(self.images['eyesdown'],  (100,))

    def draw(self, surface, camera):
        if self.ttl:
            opprect = self.current_anim.draw(surface, self.rect.move((-camera[0], -camera[1])))
            return opprect

        drawx, drawy = self.x - camera[0], self.y - camera[1]
        if self.typing: color = Color.word_select
        else: color = Color.word_unselect
        wordrect = self.word.draw(surface, (drawx, drawy - 30), color)
        opprect = self.current_anim.draw(surface, self.rect.move((-camera[0], -camera[1])))
        return wordrect.union(opprect)

    def move(self, (xt, yt)):
        if self.ttl: # flee opponent when dead: this is the inverse of Opponent.move()
            xdist = xt - self.x
            ydist = yt - self.y
            if abs(xdist) < abs(ydist): # Closer to the top or bottom edge
                if ydist < 0: self.y += self.speed
                else:         self.y -= self.speed
            else: # Closer to the left or right edge
                if xdist < 0: self.x += self.speed
                else:         self.y -= self.speed
            self.rect.center = (self.x, self.y)
        else: # call basic opponent move
            Opponent.move(self, (xt, yt))

    def tick(self, (xt, yt)):
        self.current_anim.tick()

        if self.ttl is not None:
            self.point((xt - self.x, yt - self.y), dead = True)
            self.move((xt, yt))
        else:
            self.move((xt, yt))
            if self.pause: self.current_anim = self.anims['blue']
            else: self.point((xt - self.x, yt - self.y))

    # Look your little ghosty-eyes in the correct direction.
    def point(self, (xdist, ydist), dead = False):
        if abs(xdist) > abs(ydist): # Need to move more X, look either left or right
            if xdist < 0: # Player to the left, look right
                if dead: self.current_anim = self.anims['eyesright']
                else:    self.current_anim = self.anims['left']
            else:         # Player to the right, look left
                if dead: self.current_anim = self.anims['eyesleft']
                else:    self.current_anim = self.anims['right']
        else:
            if ydist < 0: # Player above, look down
                if dead: self.current_anim = self.anims['eyesdown']
                else:    self.current_anim = self.anims['up']
            else:         # Player below, look up
                if dead: self.current_anim = self.anims['eyesup']
                else:    self.current_anim = self.anims['down']

    def destroy(self):
        self.ttl = 999 # ttl technically meaningless, but it indicates destruction
        self.speed = 9 # ghost-eyes flee the screen quickly
    
class Copter(Opponent):
    """ A flying enemy that is blocked by walls """

    name = "Copter"
    def __init__(self, word, (x, y), statics, speed = 2.5):
        super(Copter, self).__init__(word, (x, y), statics, speed)
        self.loadanims()
        self.current_anim = self.anims['fly']
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)
        self.direction = 'l'
        
        while self.collision(): # We spawned in a wall!
            self.rect.move_ip(0, -5) # move up until the hurting stops
            self.y -= 5

    @classmethod
    def loadImages(cls):
        super(Copter, cls).loadImages()

        cls.images['explosion']  = loadframes("assorted", n_of("explosion%02.f.gif", 10))       
        cls.images['fly']        = loadframes("copter", ["fly%s.gif" % i for i in xrange(1, 7)])

    def loadanims(self):
        self.anims = {}
        self.anims['fly'] = Anim(self.images['fly'], (10, 10, 10, 10, 10, 10))
        self.anims['explosion'] = Anim(self.images['explosion'], (4, 4) * 5, ends = True)
        self.anims['explosions'] = RenderUpdatesDraw([self.anims['explosion'].clone(newdelay = i * 5, newoffset = rand_offset(20)) for i in xrange(3)])

    def draw(self, surface, camera):
        if self.ttl:
            [explosion.tick() for explosion in self.anims['explosions']]
            exprects = self.anims['explosions'].draw(surface, self.rect.move(-camera[0], -camera[1])) # Need to merge into one rect
            return exprects[0].unionall(exprects[1:])
        else:
            drawx, drawy = self.x - camera[0], self.y - camera[1]
            if self.typing: color = Color.word_select
            else: color = Color.word_unselect
            wordrect = self.word.draw(surface, (drawx, drawy - 40), color)
            opprect = self.current_anim.draw(surface, self.rect.move((-camera[0], -camera[1])))
            return wordrect.union(opprect)

    def collision(self):
        for static in self.statics:
            if self.rect.colliderect(static.rect):
                return True

    def move(self, (xt, yt)):
        if self.pause:
            self.pause -= 1
            return

        xdist = xt - self.x
        ydist = yt - self.y
        dist = math.sqrt(xdist * xdist + ydist * ydist)
        nxdist, nydist = abs(xdist / dist), abs(ydist / dist)
        
        # Test whether the player is in view
        if self.direction == 'l':
            clear = clearshot((self.rect.right, self.y), (xt, yt), [o.rect for o in self.statics])
        elif self.direction == 'r':
            clear = clearshot((self.rect.left, self.y), (xt, yt), [o.rect for o in self.statics])
            
        if clear: # Probably within clear shot of player
            collidex = False
            if not -2 < xdist < 2:
                oldx = self.x
                oldrect = self.rect
                if xdist < 0:
                    self.x -= nxdist * self.speed
                else:
                    self.x += nxdist * self.speed
                self.rect.centerx, self.rect.bottom = (self.x, self.y)
                if self.collision():
                    self.x = oldx
                    self.rect = oldrect
                    collidex = True
            if not -2 < ydist < 2:
                oldy = self.y
                oldrect = self.rect
                if collidex:
                    # If we're trying to get through a wall, speed up movement in y direction
                    nydist = 1 
                if ydist < 0:
                    self.y -= nydist * self.speed
                else:
                    self.y += nydist * self.speed
                self.rect.centerx, self.rect.bottom = (self.x, self.y)
                if self.collision():
                    self.y = oldy
                    self.rect = oldrect
        else: # There be walls between us
            if yt < self.rect.top: multiplier = -1 # player above us
            else: multiplier = 1 # player below us
                
            realrect = self.rect
            self.rect = self.rect.inflate(0, 40) # Hacky!
            self.rect.move(0, multiplier * self.speed)
            if not self.collision():
                self.y += multiplier * self.speed
            else:
                if self.direction == 'l':
                    self.x -= self.speed
                elif self.direction == 'r':
                    self.x += self.speed
            self.rect = realrect
                        
        self.rect.centerx, self.rect.bottom = (self.x, self.y)

    def tick(self, (xt, yt)):
        self.current_anim.tick()
        if self.ttl is not None:
            self.ttl -= 1
            if self.ttl == 0:
                self.kill()
                return
        else:
            change_direction = random.randint(0, 100)
            if change_direction == 0:
                if self.direction == 'l': self.direction = 'r'
                elif self.direction == 'r': self.direction = 'l'
            self.move((xt, yt))

    def destroy(self):
        self.ttl = max([explosion.total_time() for explosion in self.anims['explosions']])
        
class Commando(Opponent):
    name = "Commando"
    """ Sits still waiting for the player to arrive """
    def __init__(self, word, (x, y), statics = None, speed = 2.2):
        super(Commando, self).__init__(word, (x, y), statics, speed)
        self.loadanims()
        self.current_anim = self.idleleft
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)
        
        if statics:
            while distfromground(self.rect, self.statics) > 0: # don't spawn him floating in the air
                if distfromground(self.rect, self.statics) == game_constants.big_distance:
                    break
                self.y += 1
                self.rect.centerx, self.rect.bottom = (self.x, self.y)
        
        self.direction = 'l'
        self.state = States.idle

    @classmethod
    def loadImages(cls):
        super(Commando, cls).loadImages()

        cls.images['idleright'] = loadframes("commando", ("rest1.gif", "rest2.gif"))
        cls.images['idleleft']  = flippedframes(cls.images['idleright'])

    def loadanims(self):
        self.idleright = Anim(self.images['idleright'], (30, 60))
        self.idleleft  = Anim(self.images['idleleft'],  (30, 60))
    def setanim(self):
        if self.direction == 'l':
            self.current_anim = self.idleleft
        elif self.direction == 'r':
            self.current_anim = self.idleright
    def draw(self, surface, camera):
        opprect = self.current_anim.draw(surface, self.rect.move((-camera[0], -camera[1])))
        return opprect
    def move(self, (xt, yt)):
        pass
    def tick(self, (xt, yt)):
        self.current_anim.tick()
    def typeon(self, char):
        pass # Cleverly pretend we don't respond to typing
        
class Soldier(Opponent):
    """ Runs and jumps and falls around trying to find the player """

    name = "Soldier"
    def __init__(self, word, (x, y), statics, speed = 2.2):
        super(Soldier, self).__init__(word, (x, y), statics, speed)
        self.jumpspeed = 4.5
        self.loadanims()
        self.current_anim = self.anims['runleft']
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)
        self.direction = 'l'
        self.state = States.running
        self.ttl = None # time to live when killed

    @classmethod
    def loadImages(cls):
        super(Opponent, cls).loadImages()

        cls.images['explosion'] = loadframes("assorted", n_of("explosion%02.f.gif", 10))       
        cls.images['idleright'] = loadframes("soldier", ("rest1.gif", "rest2.gif"))
        cls.images['idleleft']  = flippedframes(cls.images['idleright'])
        cls.images['runright']  = loadframes("soldier", n_of("run%i.gif", 4))
        cls.images['runleft']   = flippedframes(cls.images['runright'])
        cls.images['fallright'] = loadframes("soldier", ("fall1.gif", "fall2.gif"))
        cls.images['fallleft']  = flippedframes(cls.images['fallright'])
        cls.images['jumpright'] = loadframes("soldier", ("flip1.gif", "flip2.gif"))
        cls.images['jumpleft']  = flippedframes(cls.images['jumpright'])

    def loadanims(self):
        self.anims = {}
        self.anims['idleright']  = Anim(self.images['idleright'],  (30, 60))
        self.anims['idleleft']   = Anim(self.images['idleleft'],   (30, 60))
        
        self.anims['runright']   = Anim(self.images['runright'],   (15, 15, 15, 15))
        self.anims['runleft']    = Anim(self.images['runleft'],    (15, 15, 15, 15))
        
        self.anims['fallright']  = Anim(self.images['fallright'],  (20, 400))
        self.anims['fallleft']   = Anim(self.images['fallleft'],   (20, 400))
        
        self.anims['jumpright']  = Anim(self.images['jumpright'],  (5, 5))
        self.anims['jumpleft']   = Anim(self.images['jumpright'],  (5, 5))
        
        self.anims['explosion']  = Anim(self.images['explosion'], (4, 4) * 5, ends = True)
        self.anims['explosions'] = RenderUpdatesDraw([self.anims['explosion'].clone(newdelay = i * 5, newoffset = rand_offset(20)) for i in xrange(5)])

    def setanim(self):
        anims = {
          States.jumping : {'l' : self.anims['jumpleft'], 'r' : self.anims['jumpright']},
          States.falling : {'l' : self.anims['fallleft'], 'r' : self.anims['fallright']},
          States.running : {'l' : self.anims['runleft'],  'r' : self.anims['runright']},
        }
        self.current_anim = anims[self.state][self.direction]

    def draw(self, surface, camera):
        if self.ttl:
            [explosion.tick() for explosion in self.anims['explosions']]
            exprects = self.anims['explosions'].draw(surface, self.rect.move(-camera[0], -camera[1]))
            # Need to merge into one rect
            return exprects[0].unionall(exprects[1:])
        else:
            drawx, drawy = self.x - camera[0], self.y - camera[1]
            if self.typing: color = Color.word_select
            else: color = Color.word_unselect
            wordrect = self.word.draw(surface, (drawx, drawy - self.rect.height - 30), color)
            opprect = self.current_anim.draw(surface, self.rect.move((-camera[0], -camera[1])))
            return wordrect.union(opprect)

    def move(self, (xt, yt)):
        if self.pause:
            self.pause -= 1
        elif self.state == States.jumping:
            self.delayframes += 1
            if self.delayframes > game_constants.jumpframes:
                self.state = States.falling
            elif self.collision():
                self.state = States.falling
            else:
                self.y -= self.jumpspeed
                if self.direction == 'l':
                    self.x -= self.speed
                elif self.direction == 'r':
                    self.x += self.speed
        else:
            xdist = xt - self.x
            ydist = yt - self.y
            if abs(ydist) > 50: # we can't run directly to the player
                if self.direction == 'l': self.x -= self.speed
                elif self.direction == 'r': self.x += self.speed
            else: # take your best shot
                if not -2 < xdist < 2:
                    if xdist < 0:
                        self.x -= self.speed
                        self.direction = 'l'
                    else:
                        self.x += self.speed
                        self.direction = 'r'
                    
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)

    def tick(self, (xt, yt)):
        self.current_anim.tick()
        if self.ttl is not None:
            self.ttl -= 1
            if self.ttl == 0:
                self.kill()
                return

        dist = distfromground(self.rect, self.statics)
        if dist > 0:
            if dist > game_constants.jumpspeed: # Far from the ground
                self.y += game_constants.jumpspeed
                if self.state == States.running:
                    self.state = States.falling
                    self.anims['runright'].reset()
                    self.anims['runleft'].reset()
            else: # Hitting the ground
                self.y += dist
                self.state = States.running
        self.rect = self.current_anim.get_rect()
        self.rect.centerx, self.rect.bottom = (self.x, self.y)

        if self.state == States.running:
            jumped = False
            # FIXME: this is 80% correct, but maxjump_width/height are for the player,
            # and their math doesn't work out for soldier speed and bounding box.
            for platform in self.statics:
                if self.y - game_constants.maxjump_height < platform.rect.top < self.y:
                    if self.direction == 'l':
                        if platform.rect.right < self.x:
                            dist = self.x - platform.rect.right
                            if game_constants.maxjump_width >= dist >= 0:
                                self.jump()
                                jumped = True
                    elif self.direction == 'r':
                        if self.x < platform.rect.left:
                            dist = platform.rect.left - self.x
                            if game_constants.maxjump_width >= dist >= 0:
                                self.jump()
                                jumped = True
            if not jumped:
                change_direction = random.randint(0, 100)
                if change_direction == 0:
                    if self.direction == 'l': self.direction = 'r'
                    elif self.direction == 'r': self.direction = 'l'
        
        self.move((xt, yt)) # a little buggy but better than fixing everything else up
        
        self.setanim()

    def collision(self):
        for static in self.statics:
            if self.rect.colliderect(static.rect):
                return True

    def jump(self):
        if self.state in (States.jumping, States.falling):
            return

        self.delayframes = 0
        self.anims['jumpright'].reset()
        self.anims['jumpleft'].reset()
        self.state = States.jumping

    def destroy(self):
        self.ttl = max([explosion.total_time() for explosion in self.anims['explosions']])
