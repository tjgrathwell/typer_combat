import pygame, math, random
from pygame.locals import *
from general import Anim, game_constants, RenderUpdatesDraw, loadframes, flippedframes, n_of, WrappedSprite
from collision import distfromground, distfromceiling

class Weapons:
    """ Weapons will have different effects when typing """
    normal, shotgun, bfg = range(3)
    colors = ((0, 255, 0),
              (255, 0, 0),
              (0, 0, 255))

class States:
    """ Enum for possible states that a Player object can be in """
    jumping, idle, running, falling, shooting, hit = range(6)

class Bullet(pygame.sprite.Sprite):
    """ A short vector on the screen that is hurtling toward an opponent.
        'Start' is the world-position of the bullet's origin, 'Vector' is a world-normalized vector toward the bullet's objective
    """

    def __init__(self, shooter, weapon, start, vector, opponent, ttl):
        super(Bullet, self).__init__()
        self.ttl = ttl # time to live
        self.shooter = shooter
        self.weapon = weapon # What weapon type did this bullet come from?
        self.start = start
        self.vector = vector
        self.next = start[0] - vector[0] * game_constants.bulletspeed, start[1] - vector[1] * game_constants.bulletspeed
        self.opponent = opponent

        self.campos = None
        self.rect = None # Calculated at draw-time

    def move(self):
        self.ttl -= 1
        if self.ttl == 0:
            self.opponent.hit(self.weapon, self.shooter)
            self.kill()
            return

        self.start = self.next
        self.next = (self.start[0] - self.vector[0] * game_constants.bulletspeed, self.start[1] - self.vector[1] * game_constants.bulletspeed)

    def draw(self, surface, campos):
        # We want to be able to kill the bullet if it's out of camera,
        #   but pygame won't let us do that in draw, so we need to save
        #   it and try in move instead.
        # This is kind of a hack anyway, there shouldn't be a way for bullets to get outside
        #   the camera rect. But oh well.
        self.campos = campos

        # Calculate screenpos by subtracting camerapos and draw
        start_screenpos = self.start[0] - campos[0], self.start[1] - campos[1]
        next_screenpos = self.next[0] - campos[0], self.next[1] - campos[1]

        # HACK: I think the 'inflate' is needed because the rect returned by 'draw' doesn't respect 'width'
        self.rect = pygame.draw.line(surface, Weapons.colors[self.weapon], start_screenpos, next_screenpos, 2).inflate(2, 2)
        return self.rect

class Player(WrappedSprite):
    """ Logic, graphics and methods for a game protagonist """

    def __init__(self, position):
        super(Player, self).__init__()

        self.state = States.falling
        self.colliders = None

        self.loadanims()
        self.direction = 'r'
        self.jumpdir = 'u'
        self.moving = False
        self.delayframes = 0
        self.weapon = Weapons.normal
        self.shots_left = 0
        self.bullets = RenderUpdatesDraw()
        self.velocity = 0

        self.selected_opponent = None
        self.position = position
        self.setanim() # Also sets self.rect for collisions

    @classmethod
    def loadImages(cls):
        super(Player, cls).loadImages()

        cls.images['upright']       = loadframes("gunstar", ["gunup1.png", "gunup2.png"])
        cls.images['upleft']        = flippedframes(cls.images['upright'])
        cls.images['upsideright']   = loadframes("gunstar", ["gunupside1.png", "gunupside2.png"])
        cls.images['upsideleft']    = flippedframes(cls.images['upsideright'])
        cls.images['sideright']     = loadframes("gunstar", ["gunside1.png", "gunside2.png"])
        cls.images['sideleft']      = flippedframes(cls.images['sideright'])
        cls.images['downsideright'] = loadframes("gunstar", ["gundownside1.png", "gundownside2.png"])
        cls.images['downsideleft']  = flippedframes(cls.images['downsideright'])
        cls.images['downright']     = loadframes("gunstar", ["gundown1.png", "gundown2.png"])
        cls.images['downleft']      = flippedframes(cls.images['downright'])
        cls.images['idleright']     = loadframes("gunstar", ["rest1.png", "rest2.png"])
        cls.images['idleleft']      = flippedframes(cls.images['idleright'])
        cls.images['runright']      = loadframes("gunstar", n_of("run%i.png", 6))
        cls.images['runleft']       = flippedframes(cls.images['runright'])
        cls.images['jumpright']     = loadframes("gunstar", ["jump1.png", "jump2.png"])
        cls.images['jumpleft']      = flippedframes(cls.images['jumpright'])
        cls.images['fallright']     = loadframes("gunstar", ["jump3.png"])
        cls.images['fallleft']      = flippedframes(cls.images['fallright'])
        cls.images['hitright']      = loadframes("gunstar", ["hit1.png", "hit2.png"])
        cls.images['hitleft']       = flippedframes(cls.images['hitright'])

    def loadanims(self):
        self.anims = {
            States.shooting : {
                'upright'       : Anim(self.images['upright'],       (5, 5)),
                'upleft'        : Anim(self.images['upleft'],        (5, 5)),

                'upsideright'   : Anim(self.images['upsideright'],   (5, 5)),
                'upsideleft'    : Anim(self.images['upsideleft'],    (5, 5)),

                'sideright'     : Anim(self.images['sideright'],     (5, 5)),
                'sideleft'      : Anim(self.images['sideleft'],      (5, 5)),

                'downsideright' : Anim(self.images['downsideright'], (5, 5)),
                'downsideleft'  : Anim(self.images['downsideleft'],  (5, 5)),

                'downright'     : Anim(self.images['downright'],     (5, 5)),
                'downleft'      : Anim(self.images['downleft'],      (5, 5)),
                },
            States.idle : {
                'r'        : Anim(self.images['idleright'],     (30, 60)),
                'l'        : Anim(self.images['idleleft'],      (30, 60)),
                },
            States.running : {
                'r'        : Anim(self.images['runright'],      (14,) * 6),
                'l'        : Anim(self.images['runleft'],       (14,) * 6),
                },
            States.jumping : {
                'r'        : Anim(self.images['jumpright'],     (20, 40)),
                'l'        : Anim(self.images['jumpleft'],      (20, 40)),
                },
            States.falling : {
                'r'        : Anim(self.images['fallright'],     (20,)),
                'l'        : Anim(self.images['fallleft'],      (20,)),
                },
            States.hit     : {
                'r'        : Anim(self.images['hitright'],      (5, 5)),
                'l'        : Anim(self.images['hitleft'],       (5, 5)),
                },
            }

    def draw(self, surface, campos):
        return self.current_anim.draw(surface, self.rect.move((-campos[0], -campos[1])))

    def setanim(self): # Set animation from state and direction
        if self.state != States.shooting:
            self.current_anim = self.anims[self.state][self.direction]

        # Want to ensure that new bottom = old bottom
        self.rect = self.current_anim.get_rect()
        self.rect.bottom = int(self.position[1])
        self.rect.centerx = int(self.position[0])

    def collide(self):
        return pygame.sprite.spritecollide(self, self.colliders, False)

    def direct(self, direction):
        self.moving = True
        if direction == K_LEFT:
            self.direction = 'l'
            if self.state not in (States.jumping, States.falling, States.hit):
                self.state = States.running
        elif direction == K_RIGHT:
            self.direction = 'r'
            if self.state not in (States.jumping, States.falling, States.hit):
                self.state = States.running

    def tick(self):
        self.delayframes += 1

        if self.state in (States.falling, States.jumping, States.hit):
            if self.velocity > game_constants.terminal_velocity:
                self.velocity -= .25

        # If we're falling, check how far we are from the nearest ground. If we're further than one tick's distance,
        # move jumpspeed units. If we're closer than one tick's distance, move directly to the ground.
        if self.state in (States.falling, States.hit):
            dist = distfromground(self.rect, self.colliders)
            if dist <= abs(self.velocity):
                self.move_vertical(dist)
                if self.state == States.hit:
                    if self.delayframes > game_constants.hitframes:
                        self.moving = True
                        self.state = States.running
                elif self.moving: self.state = States.running
                else: self.state = States.idle
            else:
                self.move_vertical(-self.velocity)
        elif self.state == States.jumping:
            dist = distfromceiling(self.rect, self.colliders)
            if dist <= self.velocity:
                self.move_vertical(-dist)
                self.state = States.falling
                self.velocity = 0
            else:
                self.move_vertical(-self.velocity)
            if self.velocity <= 0 or self.collide():
                self.state = States.falling
        elif self.state == States.running:
            newdist = distfromground(self.rect, self.colliders)
            if newdist > 0:
                self.state = States.falling
            if not self.moving: self.state = States.idle # Not moving but run animation is being displayed

        if self.moving:
            jump_slow = False
            if self.state == States.jumping and self.jump_target <> None:
                # Determine if moving laterally too fast will botch the jump
                # to wit: will the top of the player rect be higher than the bottom of the platform
                # before the edge of the player closest to the platform is within the platform
                # Ugly fudge factor of five pixel units included.
                if self.direction == 'l':
                    if (self.rect.left - game_constants.speed - 5) < self.jump_target.rect.right and \
                       (self.rect.top > self.jump_target.rect.bottom):
                        jump_slow = True
                elif self.direction == 'r':
                    if (self.rect.right + game_constants.speed + 5) > self.jump_target.rect.left and \
                       (self.rect.top > self.jump_target.rect.bottom):
                        jump_slow = True

            if self.state in (States.running, States.jumping, States.falling) and not jump_slow: # Left-Right movement is allowed
                oldpos, oldrect = self.position, self.rect
                if self.direction == 'l':
                    self.move_horizontal(-game_constants.speed)
                elif self.direction == 'r':
                    self.move_horizontal(game_constants.speed)
                if self.collide():
                    self.position, self.rect = oldpos, oldrect

        self.setanim()
        self.current_anim.tick()

        if self.selected_opponent:
            self.point(self.selected_opponent) # Point weapon in direction of selected thing

        for bullet in self.bullets:
            bullet.move() # Move all the laser-things that might be on screen

        self.moving = False # Require the move() function to refresh this every tick

    # fixme: these are dumb
    def move_vertical(self, vdist):
        self.position = self.position[0], self.position[1] + vdist
        self.rect.move(0, vdist)

    def move_horizontal(self, hdist):
        self.position = self.position[0] + hdist, self.position[1]
        self.rect.move(hdist, 0)

    def idle(self):
        self.state = States.idle

    def jump(self, jump_target = None):
        if self.state in (States.jumping, States.falling): return

        self.jump_target = jump_target
        self.delayframes = 0
        self.anims[States.jumping]['r'].reset()
        self.anims[States.jumping]['l'].reset()
        self.state = States.jumping
        self.velocity = 7

    def hit(self): # Player was injured
        self.moving = False
        self.state = States.hit
        self.velocity = 0
        self.delayframes = 0

    def point(self, selected): # Point gun at some quadrant
        # 1 _|_ 2
        # 4  |  3
        if (self.state not in (States.falling, States.jumping)):
            self.state = States.shooting

        x = self.rect.center[0] - selected.x
        y = self.rect.center[1] - selected.y
        h = math.sqrt(x**2 + y**2)
        angle = math.degrees(math.asin(y / h))

        anim_name = None
        if angle > 0: # Quadrant 1 or 2
            if x < 0: # Quadrant 2: up, diag or side
                if abs(angle) < 30:
                    anim_name = 'sideright'
                elif 30 < abs(angle) < 70:
                    anim_name = 'upsideright'
                else:
                    anim_name = 'upright'
            else: # Quadrant 1: up, diag or side
                if abs(angle) < 30:
                    anim_name = 'sideleft'
                elif 30 < abs(angle) < 70:
                    anim_name = 'upsideleft'
                else:
                    anim_name = 'upleft'
        else: # Quadrant 3 or 4
            if x < 0: # Quadrant 3: side, diag or down
                if abs(angle) < 30:
                    anim_name = 'sideright'
                elif 30 < abs(angle) < 70:
                    anim_name = 'downsideright'
                else:
                    anim_name = 'downright'
            else: # Quadrant 4: side, diag or down
                if abs(angle) < 30:
                    anim_name = 'sideleft'
                elif 30 < abs(angle) < 70:
                    anim_name = 'downsideleft'
                else:
                    anim_name = 'downleft'
        self.current_anim = self.anims[States.shooting][anim_name]

    def shoot(self, selected):
        # Gunshots emerge from center of player...
        #   could later make this be exact gun position by dicting anims
        player = self.rect.center

        # Reset powerup weapons after 10 shots.
        if self.weapon != Weapons.normal:
            self.shots_left -= 1
            if self.shots_left < 0:
                self.weapon = Weapons.normal

        if self.weapon == Weapons.normal:
            shotcount = 1
        elif self.weapon == Weapons.shotgun:
            shotcount = 3

        for _ in xrange(shotcount):
            # Fudge the destination point a bit to make it look like shots are being
            #   sent out haphazardly instead of to the same point every time
            fudgex = selected.x + random.randint(-selected.rect.width / 2, selected.rect.width / 2)
            fudgey = selected.y + random.randint(-selected.rect.height / 2, selected.rect.height / 2)
            distx, disty = (player[0] - fudgex, player[1] - fudgey)
            hypotenuse = math.sqrt(distx**2 + disty**2)
            nx, ny = distx / hypotenuse, disty / hypotenuse
            ttl = int(hypotenuse / game_constants.bulletspeed)

            self.bullets.add(Bullet(
                self,
                self.weapon,
                (player[0] - nx * 4, player[1] - ny * 4),
                [nx, ny],
                selected,
                ttl))
