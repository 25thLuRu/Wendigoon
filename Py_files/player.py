import pygame
from settings import *
from support import import_folder
from entity import Entity
class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites,create_attack,destroy_attack, create_bullet):
        super().__init__(groups)
        original_image = pygame.image.load('./graphics/character/Sprite-0002downwalk.jpg').convert_alpha()
        self.image = pygame. transform.scale(original_image,(TILESIZE,TILESIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0,0)
        #movement
        self.direction = pygame.math.Vector2()
        self.attacking = False
        self.attack_cooldown = 350
        self.attack_time = None

        
        self.bullet = False
        self.bullet_cooldown = 350
        self.bullet_time = None
        self.item = False
        self.item_cooldown = 350
        self.item_time = None

        self.obstacle_sprites = obstacle_sprites
        self.k_previous = False

        self.weapon_index = 0
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        #create attack
        self.create_attack = create_attack
        self.destroy_attack = destroy_attack
        #inventory swap
        self.item_index = 0
        self.item = list(item_data.keys())[self.item_index]

        #bullet
        self.bullet_index = 0
        self.bullet_list = list(bullet_data.keys())[self.bullet_index]
        self.create_bullet = create_bullet
        #inventory swap timer
        self.can_switch = True
        self.item_switch_time = None
        self.switch_cooldown = 200


    #graphics setup
        self.import_player_assets()
        self.status = 'down'
    
    #stats
        self.stats = {'health':300, 'energy':60, 'attack':10, 'speed':3, 'sprint_energy':100, 'ammo':64}
        self.health = self.stats['health']
        self.sprint_energy = self.stats['sprint_energy']
        self.ammo = self.stats['ammo']
        self.speed = self.stats['speed']
        self.atk_base = self.stats['attack']

    #damage timer
        self.vulnerable = True
        self.hurt_time = None
        self.invincibility_duration = 500

    #movement input
    def import_player_assets(self):
        character_path = './graphics/character/'
        self.animations = {'up':[], 'down':[], 'left':[], 'right':[],
                            'right_idle':[], 'left_idle':[], 'up_idle':[], 'down_idle':[],
                            'right_attack':[], 'left_attack':[], 'up_attack':[], 'down_attack':[],
                            'right_bullet':[], 'left_bullet':[], 'up_bullet':[], 'down_bullet':[]}
        for animation in self.animations.keys():
            full_path = character_path + animation
            self.animations[animation] = import_folder(full_path)
            print(self.animations)

    def input(self):
        if not self.attacking and not self.bullet:
            keys = pygame.key.get_pressed()
            # up and down
            if keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0
            # left and right
            if keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            # NOTE: remove any handling of K_k from here.
            if keys[pygame.K_j] and not self.attacking:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                print('attack')
            # do not handle K here
            elif keys[pygame.K_e]:
                self.item = True
                self.item_time = pygame.time.get_ticks()
                print('item')
            elif keys[pygame.K_q] and self.can_switch:
                self.can_switch = False
                self.item_switch_time = pygame.time.get_ticks()
                if self.item_index < len(list(item_data.keys())) - 1:
                    self.item_index += 1
                else:
                    self.item_index = 0
                self.item = list(item_data.keys())[self.item_index]
                print('swap')
            elif keys[pygame.K_f]:
                print('interact')
    
    def get_status(self):
        #idle status
        if self.direction.x == 0 and self.direction.y == 0:
            if not 'idle' in self.status and not 'attack' in self.status and not 'bullet' in self.status and not 'item' in self.status and not 'swap' in self.status and not 'interact' in self.status:
                self.status = self.status + '_idle'
        if self.attacking:
            self.direction.x = 0
            self.direction.y = 0
            if not 'attack' in self.status:
                if 'idle' in self.status:
                    self.status = self.status.replace('_idle','_attack')
                else:
                    self.status = self.status + '_attack'
        else:
            if 'attack' in self.status:
                self.status = self.status.replace('_attack','')
        if self.bullet:
            self.direction.x = 0
            self.direction.y = 0
            if not 'bullet' in self.status:
                if 'idle' in self.status:
                    self.status = self.status.replace('_idle','_bullet')
                else:
                    self.status = self.status + '_bullet'
        else:
            if 'bullet' in self.status:
                self.status = self.status.replace('_bullet','')
                
        

    
    
    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.attacking = False
                self.destroy_attack()
        if self.bullet:
            if current_time - self.bullet_time >= self.bullet_cooldown:
                self.bullet = False
        if not self.can_switch:
            if current_time - self.item_switch_time >= self.switch_cooldown:
                self.can_switch = True
        
        if not self.vulnerable:
            if current_time - self.hurt_time >= self.invincibility_duration:
                self.vulnerable = True
    
    def animate(self):
        animation = self.animations[self.status]
        #loop over the frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center = self.hitbox.center)

        #flicker
        if not self.vulnerable:
            #flicker
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def get_full_weapon_damage(self):
        base_damage = self.atk_base
        weapon_damage = weapon_data[self.weapon]['damage']
        return base_damage + weapon_damage

    def update(self):
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate()

        keys = pygame.key.get_pressed()
        # sprint
        if keys[pygame.K_LSHIFT]:
            speed = self.speed * 2
            self.sprint_energy -= 0.5
            if self.sprint_energy <= 0:
                self.sprint_energy = 0
                speed = self.speed
        else:
            speed = self.speed
            self.sprint_energy += 0.5
            if self.sprint_energy >= self.stats['sprint_energy']:
                self.sprint_energy = self.stats['sprint_energy']
        self.move(speed)

        # ---- Single-press K detection for firing a bullet and using ammo ----
        # only trigger when key transitions from not-pressed -> pressed
        if keys[pygame.K_k] and not self.k_previous:
            # key down moment
            if self.ammo > 0 and not self.bullet:
                self.ammo -= 1
                print(f"Fired bullet — ammo left: {self.ammo}")
                # start bullet state and cooldown timer
                self.bullet = True
                self.bullet_time = pygame.time.get_ticks()
                damage = list(bullet_data.values())[self.bullet_index]['damage']
                ammo = self.ammo
                self.create_bullet(damage,ammo)
                # call any bullet creation/spawn here if needed:
                # self.create_bullet() or similar
        # update previous state (so the next frame knows if it was pressed)
        self.k_previous = keys[pygame.K_k]

        # keep ammo within the max
        if self.ammo > self.stats['ammo']:
            self.ammo = self.stats['ammo']
            
        
