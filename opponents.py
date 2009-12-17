import pygame, random, math
from general import RenderUpdatesDraw, game_constants, Color, Anim, loadframes
from player import Weapons, States
from collision import distfromground, clearshot

def rand_offset(value):
    return (random.randint(-value,value),random.randint(-value,value))
    
class Opponent(pygame.sprite.Sprite):
    """ A holder of a word, along with the game logic for moving around the screen and such. """
    name = "Nothing"
    def __init__(self,word,(x,y),statics,speed=2.0):
        pygame.sprite.Sprite.__init__(self)
        self.statics = statics
        self.word = word
        self.typing = False
        self.speed = speed
        self.pause = 0
        (self.x, self.y) = (float(x),float(y))
        self.rect = pygame.rect.Rect(0,0,5,5)
        self.rect.center = (self.x,self.y) # Smaller rect used for collision, NOT DRAWING
        self.ttl = None # Time to live when killed
    def draw(self,surface,camera):
        drawx,drawy = self.x-camera[0],self.y-camera[1]
        if self.typing: color = Color.word_select
        else: color = Color.word_unselect
        wordrect = self.word.draw(surface,(drawx,drawy-10),color)
        opprect = pygame.draw.circle(surface,(200,200,200),(int(drawx),int(drawy)),3).inflate(3,3)
        return wordrect.union(opprect)
    def hit(self, weapon, shooter):
        if weapon == Weapons.normal:
            self.pause = 20
        elif weapon == Weapons.shotgun:
            self.pause = 40
    def typeon(self,char):
        if not self.word.done():
            if char == self.word.string[0]: self.typing = True
            success = self.word.typeon(char)
            return success
    def value(self):
        return len(self.word.string)/5.0
    def move(self,(xt,yt)):
        if self.pause:
            self.pause -= 1
        else:
            xdist = xt-self.x
            ydist = yt-self.y
            dist = math.sqrt(xdist*xdist + ydist*ydist)
            nxdist, nydist = abs(xdist/dist), abs(ydist/dist)
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
    def tick(self,(xt,yt)):
        self.move((xt,yt))
    def destroy(self):
        self.kill() # remove self from all sprite lists
       
class Ghost(Opponent):
    """ A ghost can float through walls and will move on a direct line toward the player. """
    name = "Ghost"
    def __init__(self,word,(x,y),statics,speed=2.2):
        Opponent.__init__(self,word,(x,y),statics,speed)
        self.loadanims()
        self.current_anim = self.left
        self.rect = self.current_anim.get_rect()
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
    def loadanims(self):
        self.left = Anim(Ghost.images_left,(10,10))
        self.right = Anim(Ghost.images_right,(10,10))
        self.up = Anim(Ghost.images_up,(10,10))
        self.down = Anim(Ghost.images_down,(10,10))
        
        self.blue = Anim(Ghost.images_blue,(10,10))
        
        self.eyesright = Anim(Ghost.images_eyesright,([100]))
        self.eyesleft = Anim(Ghost.images_eyesleft,([100]))
        self.eyesup = Anim(Ghost.images_eyesup,([100]))
        self.eyesdown = Anim(Ghost.images_eyesdown,([100]))
    def draw(self,surface,camera):
        if self.ttl:
            opprect = self.current_anim.draw(surface,self.rect.move((-camera[0],-camera[1])))
            return opprect
        else:
            drawx,drawy = self.x-camera[0],self.y-camera[1]
            if self.typing: color = Color.word_select
            else: color = Color.word_unselect
            wordrect = self.word.draw(surface,(drawx,drawy-30),color)
            opprect = self.current_anim.draw(surface,self.rect.move((-camera[0],-camera[1])))
            return wordrect.union(opprect)
    def move(self,(xt,yt)):
        if self.ttl: # flee opponent when dead: this is the inverse of Opponent.move()
            xdist = xt-self.x
            ydist = yt-self.y
            if abs(xdist) < abs(ydist): # Closer to the top or bottom edge
                if ydist < 0: self.y += self.speed
                else: self.y -= self.speed
            else: # Closer to the left or right edge
                if xdist < 0: self.x += self.speed
                else: self.y -= self.speed
            self.rect.center = (self.x, self.y)
        else: # call basic opponent move
            Opponent.move(self,(xt,yt))
    def tick(self,(xt,yt)):
        self.current_anim.tick()
        if self.ttl is not None:
            self.point((xt-self.x,yt-self.y),dead=True)
            self.move((xt,yt))
        else:
            self.move((xt,yt))
            if self.pause: self.current_anim = self.blue
            else: self.point((xt-self.x,yt-self.y))
    def point(self,(xdist,ydist),dead=False): # Look your little ghosty-eyes in the right direction.
        if abs(xdist) > abs(ydist): # Need to move more X, look either left or right
            if xdist < 0: # Player to the left, look right
                if dead: self.current_anim = self.eyesright
                else: self.current_anim = self.left
            else:         # Player to the right, look left
                if dead: self.current_anim = self.eyesleft
                else: self.current_anim = self.right
        else:
            if ydist < 0: # Player above, look down
                if dead: self.current_anim = self.eyesdown
                else: self.current_anim = self.up
            else:         # Player below, look up
                if dead: self.current_anim = self.eyesup
                else: self.current_anim = self.down
    def destroy(self):
        self.ttl = 999 # ttl technically meaningless, but it indicates destruction
        self.speed = 9 # ghost-eyes flee the screen quickly
    
class Copter(Opponent):
    """ A flying enemy that is blocked by walls """
    name = "Copter"
    def __init__(self,word,(x,y),statics,speed=2.5):
        Opponent.__init__(self,word,(x,y),statics,speed)
        self.loadanims()
        self.current_anim = self.fly_anim
        self.rect = self.current_anim.get_rect()
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
        self.direction = 'l'
        
        while self.collision(): # We spawned in a wall!
            self.rect.move_ip(0,-5) # move up until the hurting stops
            self.y -= 5
    def loadanims(self):
        self.fly_anim = Anim(Copter.images_fly,(10,10,10,10,10,10))
        self.explosion = Anim(Assorted.images_explosion, (4,4)*5, ends=True)
        self.explosions = RenderUpdatesDraw([self.explosion.clone(newdelay=i*5,newoffset=rand_offset(20)) for i in xrange(3)])
    def draw(self,surface,camera):
        if self.ttl:
            [explosion.tick() for explosion in self.explosions]
            exprects = self.explosions.draw(surface,self.rect.move(-camera[0],-camera[1])) # Need to merge into one rect
            return exprects[0].unionall(exprects[1:])
        else:
            drawx,drawy = self.x-camera[0],self.y-camera[1]
            if self.typing: color = Color.word_select
            else: color = Color.word_unselect
            wordrect = self.word.draw(surface,(drawx,drawy-40),color)
            opprect = self.current_anim.draw(surface,self.rect.move((-camera[0],-camera[1])))
            return wordrect.union(opprect)
    def collision(self):
        for static in self.statics:
            if self.rect.colliderect(static.rect):
                return True
    def move(self,(xt,yt)):
        if self.pause:
            self.pause -= 1
        else:
            xdist = xt-self.x
            ydist = yt-self.y
            dist = math.sqrt(xdist*xdist + ydist*ydist)
            nxdist, nydist = abs(xdist/dist), abs(ydist/dist)
            
            # Test whether the player is in view
            if self.direction == 'l':
                clear = clearshot((self.rect.right,self.y),(xt,yt),[o.rect for o in self.statics])
            elif self.direction == 'r':
                clear = clearshot((self.rect.left,self.y),(xt,yt),[o.rect for o in self.statics])
                
            if clear: # Probably within clear shot of player
                collidex = False
                if not -2 < xdist < 2:
                    oldx = self.x
                    oldrect = self.rect
                    if xdist < 0:
                        self.x -= nxdist * self.speed
                    else:
                        self.x += nxdist * self.speed
                    self.rect.centerx,self.rect.bottom = (self.x, self.y)
                    if self.collision():
                        self.x = oldx
                        self.rect = oldrect
                        collidex = True
                if not -2 < ydist < 2:
                    oldy = self.y
                    oldrect = self.rect
                    if collidex: nydist = 1 # If we're trying to get through a wall, speed up movement in y direction
                    if ydist < 0:
                        self.y -= nydist * self.speed
                    else:
                        self.y += nydist * self.speed
                    self.rect.centerx,self.rect.bottom = (self.x, self.y)
                    if self.collision():
                        self.y = oldy
                        self.rect = oldrect
            else: # There be walls between us
                if yt < self.rect.top: multiplier = -1 # player above us
                else: multiplier = 1 # player below us
                    
                realrect = self.rect
                self.rect = self.rect.inflate(0,40) # Hacky!
                self.rect.move(0,multiplier*self.speed)
                if not self.collision():
                    self.y += multiplier*self.speed
                else:
                    if self.direction == 'l':
                        self.x -= self.speed
                    elif self.direction == 'r':
                        self.x += self.speed
                self.rect = realrect
                        
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
    def tick(self,(xt,yt)):
        self.current_anim.tick()
        if self.ttl is not None:
            self.ttl -= 1
            if self.ttl == 0:
                self.kill()
                return
        else:
            change_direction = random.randint(0,100)
            if change_direction == 0:
                if self.direction == 'l': self.direction = 'r'
                elif self.direction == 'r': self.direction = 'l'
            self.move((xt,yt))
    def destroy(self):
        self.ttl = max([explosion.total_time() for explosion in self.explosions])
        
class Commando(Opponent):
    name = "Commando"
    """ Sits still waiting for the player to arrive """
    def __init__(self,word,(x,y),statics=None,speed=2.2):
        Opponent.__init__(self,word,(x,y),statics,speed)
        self.loadanims()
        self.current_anim = self.idleleft
        self.rect = self.current_anim.get_rect()
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
        
        if statics:
            while distfromground(self.rect,self.statics) > 0: # don't spawn him floating in the air
                if distfromground(self.rect,self.statics) == game_constants.big_distance:
                    break
                self.y += 1
                self.rect.centerx,self.rect.bottom = (self.x, self.y)
        
        self.direction = 'l'
        self.state = States.idle
    def loadanims(self):
        self.idleright = Anim(Commando.images_idleright,(30,60))
        self.idleleft = Anim(Commando.images_idleleft,(30,60))
    def setanim(self):
        if self.direction == 'l':
            self.current_anim = self.idleleft
        elif self.direction == 'r':
            self.current_anim = self.idleright
    def draw(self,surface,camera):
        opprect = self.current_anim.draw(surface,self.rect.move((-camera[0],-camera[1])))
        return opprect
    def move(self,(xt,yt)):
        pass
    def tick(self,(xt,yt)):
        self.current_anim.tick()
    def typeon(self,char):
        pass # Cleverly pretend we don't respond to typing
        
class Soldier(Opponent):
    name = "Soldier"
    """ Runs and jumps and falls around trying to find the player """
    def __init__(self,word,(x,y),statics,speed=2.2):
        Opponent.__init__(self,word,(x,y),statics,speed)
        self.jumpspeed = 4.5
        self.loadanims()
        self.current_anim = self.runleft
        self.rect = self.current_anim.get_rect()
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
        self.direction = 'l'
        self.state = States.running
        self.ttl = None # time to live when killed
    def loadanims(self):
        self.idleright = Anim(Soldier.images_idleright,(30,60))
        self.idleleft = Anim(Soldier.images_idleleft,(30,60))
        
        self.runright = Anim(Soldier.images_runright,(15,15,15,15))
        self.runleft = Anim(Soldier.images_runleft,(15,15,15,15))
        
        self.fallright = Anim(Soldier.images_fallright,(20,400))
        self.fallleft = Anim(Soldier.images_fallleft,(20,400))
        
        self.jumpright = Anim(Soldier.images_jumpright,(5,5))
        self.jumpleft = Anim(Soldier.images_jumpright,(5,5))
        
        self.explosion = Anim(Assorted.images_explosion, (4,4)*5, ends=True)
        self.explosions = RenderUpdatesDraw([self.explosion.clone(newdelay=i*5,newoffset=rand_offset(20)) for i in xrange(5)])
    def setanim(self):
        if self.direction == 'l':
            if self.state == States.jumping:
                self.current_anim = self.jumpleft
            elif self.state == States.running:
                self.current_anim = self.runleft
            elif self.state == States.falling:
                self.current_anim = self.fallleft
        elif self.direction == 'r':
            if self.state == States.jumping:
                self.current_anim = self.jumpright
            elif self.state == States.running:
                self.current_anim = self.runright
            elif self.state == States.falling:
                self.current_anim = self.fallright
    def draw(self,surface,camera):
        if self.ttl:
            [explosion.tick() for explosion in self.explosions]
            exprects = self.explosions.draw(surface,self.rect.move(-camera[0],-camera[1])) # Need to merge into one rect
            return exprects[0].unionall(exprects[1:])
        else:
            drawx,drawy = self.x-camera[0],self.y-camera[1]
            if self.typing: color = Color.word_select
            else: color = Color.word_unselect
            wordrect = self.word.draw(surface,(drawx,drawy-self.rect.height-30),color)
            opprect = self.current_anim.draw(surface,self.rect.move((-camera[0],-camera[1])))
            return wordrect.union(opprect)
    def move(self,(xt,yt)):
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
            xdist = xt-self.x
            ydist = yt-self.y
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
        self.rect.centerx,self.rect.bottom = (self.x, self.y)
    def tick(self,(xt,yt)):
        self.current_anim.tick()
        if self.ttl is not None:
            self.ttl -= 1
            if self.ttl == 0:
                self.kill()
                return
        else:
            dist = distfromground(self.rect,self.statics)
            if dist > 0:
                if dist > game_constants.jumpspeed: # Far from the ground
                    self.y += game_constants.jumpspeed
                    if self.state == States.running:
                        self.state = States.falling
                        self.runright.reset()
                        self.runleft.reset()
                else: # Hitting the ground
                    self.y += dist
                    self.state = States.running
            self.rect = self.current_anim.get_rect()
            self.rect.centerx,self.rect.bottom = (self.x, self.y)

            if self.state == States.running:
                jumped = False
                # FIXME: this is 80% correct, but maxjump_width/height are for the player, and their math
                # doesn't work out for soldier speed and bounding box.
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
                    change_direction = random.randint(0,100)
                    if change_direction == 0:
                        if self.direction == 'l': self.direction = 'r'
                        elif self.direction == 'r': self.direction = 'l'
            
            self.move((xt,yt)) # a little buggy but better than fixing everything else up
            
            self.setanim()
    def collision(self):
        for static in self.statics:
            if self.rect.colliderect(static.rect):
                return True
    def jump(self):
        if not self.state in (States.jumping, States.falling):
            self.delayframes = 0
            self.jumpright.reset()
            self.jumpleft.reset()
            self.state = States.jumping
    def destroy(self):
        self.ttl = max([explosion.total_time() for explosion in self.explosions])
       
class Assorted: # assorted image holder
    pass