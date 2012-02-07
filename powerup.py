import pygame, general
from collision import distfromground
from general import game_constants, loadframes
from player import Weapons

class Powerup(general.WrappedSprite):
    """ A non-moving object that sits on a platform waiting to be consumed. """

    def __init__(self, position, statics):
        super(Powerup, self).__init__()

        self.x, self.y = position
        self.rect      = pygame.rect.Rect(0, 0, 0, 0)
        self.statics   = statics
        self.rect.centerx, self.rect.bottom = position

        while distfromground(self.rect, self.statics) > 0:
            # Ensure this thing is on the ground
            self.y += 1
            self.rect.bottom = self.y
            if distfromground(self.rect, self.statics) == game_constants.big_distance:
                # fallen off the screen
                self.kill()
                break

        self.image = None # needs to be overloaded by other classes
        self.loadanims()
      
    def draw(self, surface, campos):
        return self.image.draw(surface, self.rect.move((-campos[0], -campos[1])))

    def loadanims(self):
        pass

    def effect(self, player):
        pass

    def tick(self):
        self.image.tick()
        
class Shotgun(Powerup):
    @classmethod
    def loadImages(cls):
        super(Shotgun, cls).loadImages()
        cls.images['shotgun'] = loadframes("assorted", ("shotgun1.gif",))
    
    def loadanims(self):
        self.image = general.Anim(self.images['shotgun'], ([200]))
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.bottom = self.x, self.y

    def effect(self, scene, player):
        player.weapon = Weapons.shotgun
        player.shots_left = 10

class Heart(Powerup):
    @classmethod
    def loadImages(cls):
        super(Heart, cls).loadImages()
        heart_frames = [1, 2, 3, 4, 5, 4, 3, 2]
        cls.images['heart'] = loadframes("assorted", ["heart%d.gif" % i for i in heart_frames])
    
    def loadanims(self):
        self.image = general.Anim(self.images['heart'], (5, 5) * 4)
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.bottom = self.x, self.y

    def effect(self, scene, player):
        scene.health.increase()
