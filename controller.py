import pygame
import string
from general import *
from opponents import getOpponent, Commando
from pygame.locals import *
from player import States
from powerup import Heart, Shotgun
from feeder import getFeeder

directions = (K_UP, K_DOWN, K_LEFT, K_RIGHT)
specials =         "1234567890[]\;',./"
shifted_specials = "!@#$%^&*(){}|:\"<>?"
special_keys_trans_table = string.maketrans(specials,shifted_specials)

class Controller:
    """ Event and game status handler for main game. """

    def __init__(self, screen):
        from scene import LoadingScene, PlatformingScene

        loading_scene = LoadingScene(screen)
        loading_scene.draw()
        pygame.display.update()

        self.scene    = PlatformingScene(screen)
        self.player   = self.scene.player

        self.spawners = [getOpponent(opp_name) for opp_name in Options.selected_opponents]

        feed_sources = [getFeeder(feed_name) for feed_name in Options.selected_feeds]
        word_list    = [word for feeder in feed_sources for word in feeder.words]
        self.words   = WordMaker(word_list)

        self.free_movement = False
        
        self.direction         = 'r'   # What direction are we moving in
        self.spawncount        = 0     # Frame tick counter for spawn event
        self.jumpsoon          = False # Has a jump been scheduled by the player?
        self.selected_platform = None  # What platform are we scheduled to jump to

    def switchToScene(self):
        return self.scene.switch_to

    def handleKeydown(self, key):
        shifting = (pygame.key.get_mods() & KMOD_SHIFT)

        if (self.scene.challenging):
            pass # do some other stuff with ChallengeScene

        if key in (K_LCTRL,K_RCTRL):
            self.unselect() # Release selected object
        elif key == K_SPACE:
            self.key_space()
        elif key in directions:
            self.keydown_direction(key)
        elif key == K_END: # Toggle player free movement
            self.toggle_free_movement()
        elif key in range(256): # ASCII character
            key_chr = chr(key)
            if key_chr in string.lowercase: # Word character
                self.type_normal(key_chr)
            elif key_chr in specials+shifted_specials: # Special character (,.@# etc)
                if not shifting:
                    self.type_special(key_chr)
                else:
                    self.type_special(key_chr.translate(special_keys_trans_table))

    def handleKeyup(self, key):
        if key in directions:
            self.keyup_direction(key)

    def auto_move_player(self):
        if self.player.state not in (States.shooting, States.jumping):
            # Player is capable of making a jump
            if self.jumpsoon:
                # A jump has been scheduled
                if self.direction == 'r':
                    if self.player.rect.right > self.jumppos:
                        # Distance less than the maximum jump distance
                        self.player.jump(self.selected_platform)
                        self.clear_jump()
                elif self.direction == 'l':
                    if self.player.rect.left < self.jumppos:
                        # Distance less than the maximum jump distance
                        self.player.jump(self.selected_platform)
                        self.clear_jump()
                        
        if self.player.state is not States.shooting:
            # Player is capable of movement
            if self.direction == 'r':
                self.player.direct(K_RIGHT)
            elif self.direction == 'l':
                self.player.direct(K_LEFT)

    def lazy_redraw(self):
        return self.scene.lazy_redraw()

    def tick(self, elapsed):
        if not self.free_movement:
            self.auto_move_player()

        self.collide_player_with_enemies()

        self.collide_player_with_powerups()

        self.spawn_enemies()

        self.scene.tick(elapsed)

    def draw(self):
        return self.scene.draw()

    def key_space(self):
        if (self.free_movement):
            self.player.jump()
        else:
            self.change_direction()

    def keydown_direction(self, key):
        if (self.free_movement):
            self.scene.movelist.append(key)

    def keyup_direction(self, key):
        if (self.free_movement):
            self.scene.movelist.remove(key)

    def toggle_free_movement(self):
        self.free_movement = not self.free_movement

    def clear_jump(self):
        self.jumppos = None
        self.jumpsoon = False
        if (self.selected_platform):
            self.selected_platform.selected = False     
            self.selected_platform = None   

    def collide_player_with_enemies(self):
        # TODO Retool this so it's more robust
        colliders = pygame.sprite.spritecollide(self.player, self.scene.actives, True)

        collision_hurt = False    # Was the collision with an actual, living enemy
        collision_special = False # Was the collision with a commando

        for enemy in colliders:
            if isinstance(enemy, Commando):
                collision_special = True
            elif enemy.ttl is None: # Enemies ttl is none if they haven't died
                collision_hurt = True
        if collision_hurt:
            if self.player.selected_opponent in colliders:
                # Make sure the enemy isn't selected anymore
                self.player.selected_opponent = None
            if (self.player.state != States.hit):
                # Decrease player's health and play hit animation
                self.scene.health.decrease()
                self.player.hit()
        if collision_special:
            self.scene.challenging = True
            return

    def collide_player_with_powerups(self):
        powerups = pygame.sprite.spritecollide(self.player, self.scene.powerups, True)
        for powerup in powerups:
            powerup.effect(self.scene, self.player)

    def spawn_enemies(self):            
        def spawnspot(position, direction = None):
            # Spawn more enemies in the direction the player is headed
            left_offset  = random.randint(-game_constants.w, -game_constants.w / 2)
            right_offset = random.randint(game_constants.w / 2, game_constants.w)

            if direction is None:
                xpos = position[0] + random.choice([left_offset, right_offset])
            elif direction == 'l':
                xpos = position[0] + left_offset
            elif direction == 'r':
                xpos = position[0] + right_offset
                
            ypos = position[1] - random.randint(game_constants.h / 6, game_constants.h / 5)
                
            return (xpos, ypos)
    
        self.spawncount += 1

        # Rough value used for spawning of new opponents
        level = (int(self.scene.score.score) / 10) + 5
        if self.spawncount <= 120 / (.20 * level):
            return

        self.spawncount = 0

        if len(self.scene.actives) > game_constants.max_enemies:
            return
    
        characters_in_use = list(set([enemy.word.string[0] for enemy in self.scene.actives]))

        next_word = self.words.next_word(characters_in_use)

        if self.player.state in (States.idle, States.shooting):
            # Player is standing still: Spawn equally likely to each side
            spawnpos = spawnspot(self.player.position)
        else:
            # Player is moving: Spawn in direction player is moving to
            spawnpos = spawnspot(self.player.position, self.player.direction)

        if len(self.spawners):
            EnemyType = random.choice(self.spawners) # 1/n chance of all enemy types
            self.scene.actives.add(EnemyType(next_word, spawnpos, self.scene.statics))

    def command(self, key):
        platform = self.scene.type_special(key)
        if not platform: return

        platform.selected = True
        self.selected_platform = platform
        self.jumpsoon = True
        if self.direction == 'r':
            if self.player.rect.right < platform.rect.left:
                self.jumppos = platform.rect.left - game_constants.maxjump_width
            else:
                self.direction = 'l'
                self.jumppos = platform.rect.right + game_constants.maxjump_width
        elif self.direction == 'l':
            if self.player.rect.left > platform.rect.right:
                self.jumppos = platform.rect.right + game_constants.maxjump_width
            else:
                self.direction = 'r'
                self.jumppos = platform.rect.left - game_constants.maxjump_width

    def change_direction(self):
        if self.direction == 'l':
            self.direction = 'r'
        elif self.direction == 'r':
            self.direction = 'l'
        self.clear_jump()

    def _find_opponent_for_key(self, key):
        for opponent in self.scene.actives: # Try to shoot everyone!
            hit = opponent.typeon(key)
            if hit:
                self.player.selected_opponent = opponent
                break
        if not self.player.selected_opponent:
            self.scene.score.miss()
        else:
            self.player.shoot(self.player.selected_opponent)

    def _shoot_currently_targeted_opponent(self, key):
        hit = self.player.selected_opponent.typeon(key)
        if not hit:
            self.scene.score.miss()
            return

        self.player.shoot(self.player.selected_opponent)
        if self.player.selected_opponent.defeated():
            # If we killed who we're shooting at
            self.scene.score.increase(self.player.selected_opponent.value())
            # Set up death animation, kill sprite eventually
            self.player.selected_opponent.destroy()
            self.player.idle()
            
            if random.randint(0, 10) < 3: # Spawn a powerup when enemies die, sometimes.
                spawnpos = self.player.selected_opponent.rect.center
                if random.randint(0, 5) < 2:
                    powerup = Shotgun
                else:
                    powerup = Heart
                self.scene.powerups.add(powerup(spawnpos, self.scene.statics))

            self.player.selected_opponent = None

    def type_normal(self, key):
        if not self.player.selected_opponent:
            self._find_opponent_for_key(key) 
        else:
            self._shoot_currently_targeted_opponent(key)

    def type_special(self, key):
        if self.player.state in (States.falling, States.jumping):
            return
        
        self.command(key)

    def unselect(self):
        if self.player.selected_opponent:
            self.player.selected_opponent.release()
            self.player.selected_opponent = None
        self.player.idle()
