import pygame
from settings import *
from entity import Entity
from support import *

class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, obstacle_sprites, damage_player):
        super().__init__(groups)
        self.sprite_type = 'enemy'

        # graphics
        self.import_graphics(monster_name)
        self.status = 'down'
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations[self.status][self.frame_index]

        # stats
        self.monster_name = monster_name
        monster_info = enemy_data[self.monster_name]
        self.health = monster_info['health']
        self.damage = monster_info['damage']
        self.speed = monster_info['speed']
        self.resistance = monster_info['resistance']
        self.attack_radius = monster_info['attack_radius']
        self.notice_radius = monster_info['notice_radius']
        self.attack_type = monster_info['attack_type']

        # movement and positioning
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
        self.obstacle_sprites = obstacle_sprites

        # attack logic
        self.attacking = False
        self.attack_cooldown = 1000  # ms between shots
        self.attack_time = 0
        self.damage_player = damage_player

        # invincibility
        self.vulnerable = True
        self.hit_time = None
        self.invincibility_duration = 300

        # movement
        self.direction = pygame.math.Vector2(0, 0)

    # --------------------------
    # GRAPHICS
    # --------------------------
    def import_graphics(self, name):
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
            'right_attack': [], 'left_attack': [], 'up_attack': [], 'down_attack': []
        }

        base_path = f'./graphics/enemy/{name}/'
        for animation in self.animations.keys():
            full_path = base_path + animation
            self.animations[animation] = import_folder(full_path, scale=(128, 128))
            if name == 'brute':
                self.animations[animation] = import_folder(full_path, scale=(150, 150))
            elif name == 'chaser':
                self.animations[animation] = import_folder(full_path, scale=(100, 100))
            elif name == 'ranger':
                self.animations[animation] = import_folder(full_path, scale=(80, 80))
            print(f"[{name}] Loaded {len(self.animations[animation])} frames for {animation}")

    # --------------------------
    # ENEMY BEHAVIOR
    # --------------------------
    def get_player_distance_direction(self, player):
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player.rect.center)
        distance = (player_vec - enemy_vec).magnitude()

        if distance > 0:
            direction = (player_vec - enemy_vec).normalize()
        else:
            direction = pygame.math.Vector2()

        return distance, direction

    def get_status(self, player):
        distance, direction = self.get_player_distance_direction(player)

        # Facing direction
        if abs(direction.x) > abs(direction.y):
            dir_name = 'right' if direction.x > 0 else 'left'
        else:
            dir_name = 'down' if direction.y > 0 else 'up'

        # Maintain attack animation if attacking
        if self.attacking:
            self.status = f"{dir_name}_attack"
        elif distance <= self.notice_radius:
            self.status = dir_name
        else:
            self.status = f"{dir_name}_idle"

    def actions(self, player):
        distance, direction = self.get_player_distance_direction(player)

        if self.attack_type == 'ranged':
            if self.attacking:
                # Stop all motion while attacking
                self.direction = pygame.math.Vector2()
                return

            # Within shooting range
            if distance <= self.attack_radius:
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.direction = pygame.math.Vector2()  # stop movement
                self.shoot_projectile(player)
            # Move closer if too far
            elif distance < self.notice_radius and distance > self.attack_radius * 1.2:
                self.direction = direction
            # Move away if too close
            elif distance < self.attack_radius * 0.8:
                self.direction = -direction
            else:
                self.direction = pygame.math.Vector2()

        # --- Melee enemy behavior (brute) ---
        if self.attacking:
            self.direction = pygame.math.Vector2()
            return

            # get distance and direction
        distance, direction = self.get_player_distance_direction(player)

        if distance <= self.attack_radius:
            # within range, attack
            self.attacking = True
            self.attack_time = pygame.time.get_ticks()
            self.direction = pygame.math.Vector2()  # stop movement

        # set status to attack direction
            if abs(direction.x) > abs(direction.y):
                dir_name = 'right' if direction.x > 0 else 'left'
            else:
                dir_name = 'down' if direction.y > 0 else 'up'

            self.status = f"{dir_name}_attack"
            self.damage_player(self.damage, self.attack_type)
        elif distance < self.notice_radius:
            # move toward player
            self.direction = direction
        else:
            self.direction = pygame.math.Vector2()

    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if self.attacking and current_time - self.attack_time >= self.attack_cooldown:
            self.attacking = False

        if not self.vulnerable and current_time - self.hit_time >= self.invincibility_duration:
            self.vulnerable = True

    def get_damage(self, source, attack_type):
        if self.vulnerable:
            if hasattr(source, "rect"):
                self.direction = self.get_player_distance_direction(source)[1]

            if attack_type == 'weapon':
                damage = source.get_full_weapon_damage()
            elif attack_type == 'bullet':
                damage = source
            else:
                damage = 0

            self.health -= damage
            self.hit_time = pygame.time.get_ticks()
            self.vulnerable = False

            print(f"{self.monster_name} took {damage} damage from {attack_type}. Remaining HP: {self.health}")

    def check_death(self):
        if self.health <= 0:
            self.kill()

    def hit_reaction(self):
        if not self.vulnerable:
            self.direction *= -self.resistance

    def shoot_projectile(self, player):
        direction = self.get_player_distance_direction(player)[1]
        if hasattr(self, "create_enemy_bullet"):
            self.create_enemy_bullet(self.rect.center, direction, self.damage)
            print(f"{self.monster_name} shoots towards {direction}")

    # --------------------------
    # ANIMATION
    # --------------------------
    def animate(self):
        animation = self.animations.get(self.status, [])
        if not animation:
            animation = self.animations.get('down_idle', [])
            if not animation:
                return

        self.frame_index += self.animation_speed

        if 'attack' in self.status:
            if self.frame_index >= len(animation):
                self.frame_index = 0
                # after attack animation ends, stay idle
                if not self.attacking:
                    self.status = self.status.replace('_attack', '_idle')
        else:
            if self.frame_index >= len(animation):
                self.frame_index = 0

        frame = int(self.frame_index) % len(animation)
        self.image = animation[frame]
        self.rect = self.image.get_rect(center=self.hitbox.center)

        if not self.vulnerable:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    # --------------------------
    # UPDATE
    # --------------------------
    def update(self):
        self.hit_reaction()
        self.cooldowns()

        # stop during attack
        if not self.attacking:
            self.move(self.speed)
        else:
            self.direction = pygame.math.Vector2()

        self.animate()
        self.check_death()

    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)
