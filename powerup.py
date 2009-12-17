import pygame
from collision import distfromground
from general import Anim, game_constants
from player import Weapons

class Powerup(pygame.sprite.Sprite):
    """ A non-moving object that sits on a platform waiting to be consumed. """
    def __init__(self,position,statics):
        pygame.sprite.Sprite.__init__(self)
        self.x, self.y = position
        self.rect = pygame.rect.Rect(0,0,0,0)
        self.rect.centerx, self.rect.bottom = self.x, self.y
        self.statics = statics
        while distfromground(self.rect,self.statics) > 0: # Ensure this thing is on the ground
            self.y += 1
            self.rect.bottom = self.y
            if distfromground(self.rect,self.statics) == game_constants.big_distance: # magic numbers bad
                self.kill()
                break
        self.image = None # needs to be overloaded by other classes
        self.loadanims()
    def draw(self,surface,campos):
        return self.image.draw(surface,self.rect.move((-campos[0],-campos[1])))
    def loadanims(self):
        pass
    def effect(self,player):
        pass
    def tick(self):
        self.image.tick()
        
class Shotgun(Powerup):
    def loadanims(self):
        self.image = Anim(Shotgun.images_shotgun,([200]))
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.bottom = self.x, self.y
    def effect(self,scene,player):
        player.weapon = Weapons.shotgun
        player.shots_left = 10
     
class Heart(Powerup):
    def loadanims(self):
        self.image = Anim(Heart.images_heart,(5,5)*4)
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.bottom = self.x, self.y
    def effect(self,scene,player):
        scene.health.increase()