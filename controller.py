import pygame
from general import *
from opponents import Commando
from pygame.locals import *
from player import States
from powerup import Heart, Shotgun

class Controller:
    """ Event and game status handler for main game. """

    def __init__(self, scene, words, sentences):
        self.scene = scene
        self.player = scene.player
        self.words = words
        self.sentences = sentences
        
        self.direction = 'r'# What direction are we moving in
        self.spawncount = 0 # Frame tick counter for  spawn event
        self.jumpsoon = False # Has a jump been scheduled by the player
        self.selected_platform = None # What platform are we scheduled to jump to

    def tick(self):
        if self.player.state not in (States.shooting, States.jumping): # Player is capable of making a jump
            if self.jumpsoon: # A jump has been scheduled
                if self.direction == 'r':
                    if self.player.rect.right > self.jumppos: # Distance less than the maximum jump distance
                        self.player.jump(self.selected_platform)
                        self.clear_jump()
                elif self.direction == 'l':
                    if self.player.rect.left < self.jumppos: # Distance less than the maximum jump distance
                        self.player.jump(self.selected_platform)
                        self.clear_jump()
                        
        if self.player.state is not States.shooting: # Player is capable of movement
            if self.direction == 'r':
                self.player.direct(K_RIGHT)
            elif self.direction == 'l':
                self.player.direct(K_LEFT)

    def clear_jump(self):
        self.jumppos = None
        self.jumpsoon = False
        if (self.selected_platform):
            self.selected_platform.selected = False     
            self.selected_platform = None   

    def tock(self, spawners):
        # See if any enemies are colliding with the player, kill them if so
        # TODO Retool this so it's more robust
        colliders = pygame.sprite.spritecollide(self.player, self.scene.actives, True)
        collision_hurt = False # Was the collision with an actual, living enemy
        collision_special = False # Was the collision with a commando
        for enemy in colliders:
            if isinstance(enemy, Commando):
                collision_special = True
            elif enemy.ttl is None: # Enemies ttl is none if they haven't died
                collision_hurt = True
        if collision_hurt:
            if self.player.selected_opponent in colliders: # Make sure the enemy isn't selected anymore
                self.player.selected_opponent = None
            if (self.player.state != States.hit): # Decrease player's health and play hit animation
                self.scene.health.decrease()
                self.player.hit()
        if collision_special:
            self.scene.challenging = True
            return
                
        # See if any powerups are colliding with the player, give the player their effect if so
        powerup = pygame.sprite.spritecollide(self.player, self.scene.powerups, True)
        for thing in powerup:
            thing.effect(self.scene, self.player)
            
        def spawnspot(position, direction = None):
            # Spawn more enemies in the direction the player is headed
            if direction is None:
                xpos = position[0] + random.choice([random.randint(-game_constants.w, -game_constants.w / 2), random.randint(game_constants.w / 2, game_constants.w)])
            elif direction == 'l':
                xpos = position[0] + random.randint(-game_constants.w, -game_constants.w / 2)
            elif direction == 'r':
                xpos = position[0] + random.randint(game_constants.w / 2, game_constants.w)
                
            ypos = position[1] - random.randint(game_constants.h / 6, game_constants.h / 5)
                
            return (xpos, ypos)
    
        self.spawncount += 1
        level = (int(self.scene.score.score) / 10) + 5 # Calculate rough value used for spawning of new opponents
        if self.spawncount > 120 / (.20 * level):
            self.spawncount = 0
            def word_check(word): # Does this new word have the same starting letter of any of the words we're currently using?
                for enemy in self.scene.actives:
                    if enemy.word.string[0] == word.string[0]:
                        return False
                return True

            if len(self.scene.actives) > game_constants.max_enemies:
                return
        
            next_word = self.words.next_word()
            while not word_check(next_word):
                next_word = self.words.next_word()

            if self.player.state in (States.idle, States.shooting): # Player is standing still: Spawn equally likely to each side
                spawnpos = spawnspot(self.player.position)
            else: # Player is moving: Spawn in direction player is moving to
                spawnpos = spawnspot(self.player.position, self.player.direction)

            if len(spawners):
                EnemyType = random.choice(spawners) # 1/n chance of all enemy types
                self.scene.actives.add(EnemyType(next_word, spawnpos, self.scene.statics))

    def command(self, key):
        result = self.scene.type_special(key) # Return a platform if it corresponds with the key typed
        if result:
            result.selected = True
            self.selected_platform = result
            self.jumpsoon = True
            if self.direction == 'r':
                if self.player.rect.right < result.rect.left:
                    self.jumppos = result.rect.left - game_constants.maxjump_width
                else:
                    self.direction = 'l'
                    self.jumppos = result.rect.right + game_constants.maxjump_width
            elif self.direction == 'l':
                if self.player.rect.left > result.rect.right:
                    self.jumppos = result.rect.right + game_constants.maxjump_width
                else:
                    self.direction = 'r'
                    self.jumppos = result.rect.left - game_constants.maxjump_width

    def change_direction(self):
        if self.direction == 'l':
            self.direction = 'r'
        elif self.direction == 'r':
            self.direction = 'l'
        self.clear_jump()

    def type_normal(self, key):
        if not self.player.selected_opponent: # If we aren't shooting at anything in particular
            for opponent in self.scene.actives: # Try to shoot everyone!
                hit = opponent.typeon(key)
                if hit:
                    self.player.selected_opponent = opponent
                    break
            if not self.player.selected_opponent:
                self.scene.score.miss()
            else:
                self.player.shoot(self.player.selected_opponent)
        else: # If we've previously chosen an opponent to shoot
            hit = self.player.selected_opponent.typeon(key)
            if hit:
                self.player.shoot(self.player.selected_opponent)
                if self.player.selected_opponent.defeated(): # If we killed who we're shooting at
                    self.scene.score.increase(self.player.selected_opponent.value())
                    self.player.selected_opponent.destroy() # Set up death animation, kill sprite eventually
                    self.scene.player.idle()
                    
                    if random.randint(0, 10) < 3: # Spawn a powerup when enemies die, sometimes.
                        spawnpos = self.player.selected_opponent.rect.center
                        if random.randint(0, 5) < 2:
                            PowerUp = Shotgun
                        else:
                            PowerUp = Heart
                        self.scene.powerups.add(PowerUp(spawnpos, self.scene.statics))

                    self.player.selected_opponent = None

            else:
                self.scene.score.miss()

    def type_special(self, key):
        if self.scene.player.state in (States.falling, States.jumping):
            return
        
        self.command(key)

    def unselect(self):
        if self.player.selected_opponent:
            self.player.selected_opponent.release()
            self.player.selected_opponent = None
        self.scene.player.idle()
