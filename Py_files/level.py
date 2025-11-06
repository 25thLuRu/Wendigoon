import pygame
from settings import *
from tile import Tile
from player import Player
from debug import debug
from weapons import Weapon
from ui import UI
from enemy import Enemy
from bullet import Bullet
from support import *
from random import choice
pygame.init()
pygame.mixer.init()

bgmusic = pygame.mixer.Sound('./audio/melancholia.mp3')
bgmusic.play(loops = -1)

class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()

        # group sprite setup
        self.visible_sprites = YsortCameraGroup()
        self.obstacles_sprites = pygame.sprite.Group()

        # attack sprites
        self.current_attack = None
        self.attack_sprites = pygame.sprite.Group()  # includes player + enemy bullets
        self.attackable_sprites = pygame.sprite.Group()

        self.create_map()
        self.ui = UI()
        self.wave_number = 1
        self.max_waves = 5
        self.wave_active = False
        self.wave_cleared = True
        self.wave_start_time = 0
        self.wave_delay = 3000
        #conditions
        self.game_over = False
        self.victory = False
        self.font = pygame.font.Font(None, 80)
        self.fade_alpha = 0

    def create_map(self):
        layouts = {
            'boundary': import_csv_layout('../map/map_FloorBlocks.csv'),
            'grass': import_csv_layout('../map/map_Grass.csv'),
            
        }

        graphics = {
            'grass': import_folder('graphics/grass'),
            'objects': import_folder('graphics/objects')
        }

        for style, layout in layouts.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILESIZE
                        y = row_index * TILESIZE

                        if style == 'boundary':
                            Tile((x, y), [self.obstacles_sprites], 'invisible')

                        

                        elif style == 'object':
                            if int(col) < len(graphics['objects']):
                                surf = graphics['objects'][int(col)]
                            else:
                                #  fallback if object index missing
                                surf = pygame.Surface((TILESIZE, TILESIZE))
                                surf.fill('gray')
                            Tile((x, y), [self.visible_sprites, self.obstacles_sprites], 'object', surf)

    #  Create player
        self.player = Player(
            (2000, 1430),
            [self.visible_sprites],
            self.obstacles_sprites,
            self.create_attack,
            self.destroy_attack,
            self.create_bullet
        )

    # ------------------------------
    # PLAYER ATTACK FUNCTIONS
    # ------------------------------
    def create_attack(self):
        self.current_attack = Weapon(self.player, [self.visible_sprites, self.attack_sprites])

    def destroy_attack(self):
        if self.current_attack:
            self.current_attack.kill()
        self.current_attack = None

    def create_bullet(self, damage, ammo):
        direction = self.player.direction
        if direction.length() == 0:
            direction = pygame.math.Vector2(0, -1)
        Bullet(
            self.player.rect.center,
            direction,
            [self.visible_sprites, self.attack_sprites],
            damage,
            self.obstacles_sprites
        )

    # ------------------------------
    # ENEMY RANGED ATTACK
    # ------------------------------
    def enemy_shoot(self, enemy, target):
        """Make ranger enemies fire bullets toward the player."""
        if not hasattr(enemy, "attack_time"):
            enemy.attack_time = 0
        current_time = pygame.time.get_ticks()

        if current_time - enemy.attack_time > enemy.attack_cooldown:
            enemy.attack_time = current_time

            # Compute direction toward player
            direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(enemy.rect.center)
            if direction.length() > 0:
                direction = direction.normalize()

            # Create bullet going toward the player
            bullet_damage = enemy.damage
            Bullet(
                enemy.rect.center,
                direction,
                [self.visible_sprites, self.attack_sprites],
                bullet_damage,
                self.obstacles_sprites,
                owner="enemy"  # mark owner so it doesn’t hit other enemies
            )

    def spawn_wave(self, wave_number):
        """Spawn enemies around the player, inside the map, avoiding walls."""
        print(f"🌊 Starting Wave {wave_number}")
        self.wave_active = True
        self.wave_cleared = False

        import random

        # More enemies per wave (scaling)
        num_brutes = wave_number * 3
        num_rangers = max(2, wave_number)
        num_chasers = max(1, wave_number)
        total_enemies = num_brutes + num_rangers + num_chasers

        # --- Get map boundaries ---
        min_x, max_x = 200, 3800
        min_y, max_y = 200, 2200

        # --- Get obstacle rects to avoid ---
        obstacle_rects = [sprite.rect for sprite in self.obstacles_sprites]

        # --- Define spawn ring around the player ---
        player_x, player_y = self.player.rect.center
        min_spawn_distance = 300    # not too close
        max_spawn_distance = 800    # not too far

        spawn_positions = []

        # Try until we have enough safe spawn positions
        attempts = 0
        while len(spawn_positions) < total_enemies and attempts < 2000:
            attempts += 1

            # Random angle around the player
            angle = random.uniform(0, 360)
            distance = random.randint(min_spawn_distance, max_spawn_distance)
            offset_x = int(distance * pygame.math.Vector2(1, 0).rotate(angle).x)
            offset_y = int(distance * pygame.math.Vector2(1, 0).rotate(angle).y)

            x = player_x + offset_x
            y = player_y + offset_y

            # Keep within map bounds
            if not (min_x < x < max_x and min_y < y < max_y):
                continue

            # Avoid obstacles
            enemy_rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
            if any(enemy_rect.colliderect(obs) for obs in obstacle_rects):
                continue

            spawn_positions.append((x, y))

        print(f"✅ Spawning {len(spawn_positions)} enemies around player")

        idx = 0
        for i in range(num_brutes):
            Enemy('brute', spawn_positions[idx],
                  [self.visible_sprites, self.attackable_sprites],
                  self.obstacles_sprites,
                  self.damage_player)
            idx += 1

        for i in range(num_rangers):
            Enemy('ranger', spawn_positions[idx],
                [self.visible_sprites, self.attackable_sprites],
                self.obstacles_sprites,
                self.damage_player)
            idx += 1

        for i in range(num_chasers):
            Enemy('chaser', spawn_positions[idx],
                [self.visible_sprites, self.attackable_sprites],
                self.obstacles_sprites,
                self.damage_player)
            idx += 1

    # ------------------------------
    # DAMAGE LOGIC
    # ------------------------------
    def player_attack_logic(self):
        for attack_sprite in self.attack_sprites:
            # check what the bullet/weapon hit
            collision_sprites = pygame.sprite.spritecollide(attack_sprite, self.attackable_sprites, False)
            for target_sprite in collision_sprites:
                if hasattr(attack_sprite, "sprite_type") and attack_sprite.sprite_type == "bullet":
                    # prevent friendly fire
                    if attack_sprite.owner == "player" and getattr(target_sprite, "sprite_type", "") == "enemy":
                        target_sprite.get_damage(attack_sprite.damage, "bullet")
                        attack_sprite.kill()
                    elif attack_sprite.owner == "enemy" and getattr(target_sprite, "sprite_type", "") == "player":
                        self.damage_player(attack_sprite.damage, "bullet")
                        attack_sprite.kill()
                else:
                    # melee or other attacks
                    target_sprite.get_damage(self.player, attack_sprite.sprite_type)

        # Enemy bullet hitting player
        for attack_sprite in self.attack_sprites:
            if hasattr(attack_sprite, "owner") and attack_sprite.owner == "enemy":
                if attack_sprite.rect.colliderect(self.player.rect):
                    self.damage_player(attack_sprite.damage, "bullet")
                    attack_sprite.kill()

    def damage_player(self, amount, attack_type):
        if self.player.vulnerable:
            self.player.health -= amount
            self.player.vulnerable = False
            self.player.hurt_time = pygame.time.get_ticks()

    # ------------------------------
    # GAME LOOP
    # ------------------------------
    def run(self):
        self.visible_sprites.update()
        self.visible_sprites.enemy_update(self.player)

        # Make rangers shoot bullets
        for sprite in self.visible_sprites.sprites():
            if hasattr(sprite, "monster_name") and sprite.monster_name == "ranger":
                # ranger fires if player is within notice radius
                distance = pygame.math.Vector2(sprite.rect.center).distance_to(self.player.rect.center)
                if distance <= sprite.notice_radius:
                    self.enemy_shoot(sprite, self.player)
        
        # ---------------------
        #  WAVE SYSTEM LOGIC
        # ---------------------
        if not self.wave_active and self.wave_number <= self.max_waves:
            current_time = pygame.time.get_ticks()
            if self.wave_cleared and current_time - self.wave_start_time > self.wave_delay:
                self.spawn_wave(self.wave_number)

        # Check if all enemies are dead
        enemies_left = [
            s for s in self.visible_sprites.sprites()
            if hasattr(s, "sprite_type") and s.sprite_type == "enemy"
        ]
        if self.wave_active and not enemies_left:
            print(f" Wave {self.wave_number} cleared!")
            self.wave_active = False
            self.wave_cleared = True
            self.wave_start_time = pygame.time.get_ticks()
            self.wave_number += 1

        # End after final wave
        if self.wave_number > self.max_waves and not self.wave_active:
            print("🎉 All waves completed! You win!")

        self.visible_sprites.custom_draw(self.player)
        self.player_attack_logic()

        # debug info
        debug(self.player.status)
        self.ui.display(self.player)

        font = pygame.font.Font(None, 36)
        wave_text = f"Wave: {min(self.wave_number, self.max_waves)}/{self.max_waves}"
        text_surface = font.render(wave_text, True, (255, 255, 255))
        self.display_surface.blit(text_surface, (1100, 30))
        if self.player.health <= 0 and not self.game_over:
            self.game_over = True

        if self.wave_number > self.max_waves and not self.wave_active and not self.victory:
            self.victory = True

        # --- Handle End Screens ---
        if self.victory:
            self.display_end_screen("YOU WIN!", color=(50, 255, 50))
        elif self.game_over:
            self.display_end_screen("YOU DIED", color=(255, 50, 50), show_retry=True)
        


    def display_end_screen(self, text, color=(255, 255, 255), show_retry=False):
        """Gradually darken screen and show victory/defeat message with optional retry UI."""

        # --- Gradual fade-in ---
        if self.fade_alpha < 255:
            self.fade_alpha += 5  # Increase alpha each frame
        overlay = pygame.Surface(self.display_surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.fade_alpha))  # (R,G,B,Alpha)
        self.display_surface.blit(overlay, (0, 0))

        # --- Main text ---
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(center=(self.display_surface.get_width() // 2,
                                        self.display_surface.get_height() // 2))
        self.display_surface.blit(surface, rect)

        # --- Optional retry/quit options ---
        if show_retry and self.fade_alpha >= 180:  # Only show when fade is complete
            small_font = pygame.font.Font(None, 40)
            msg_surface = small_font.render("Press [R] to Retry or [Q] to Quit", True, (255, 255, 255))
            msg_rect = msg_surface.get_rect(center=(self.display_surface.get_width() // 2,
                                                    self.display_surface.get_height() // 2 + 80))
            self.display_surface.blit(msg_surface, msg_rect)

            # Handle input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.reset_game()
            elif keys[pygame.K_q]:
                pygame.quit()
                exit()
    
    def reset_game(self):
        """Reset the game to the first wave after death."""
        self.wave_number = 1
        self.wave_active = False
        self.wave_cleared = True
        self.wave_start_time = pygame.time.get_ticks()
        self.player.health = self.player.stats['health']  # reset player HP
        self.game_over = False
        self.victory = False

        # Kill all enemies and attacks
        for sprite in self.visible_sprites.sprites():
            if getattr(sprite, "sprite_type", "") == "enemy":
                sprite.kill()
        for bullet in self.attack_sprites.sprites():
            bullet.kill()

        print("🔁 Game Reset: Restarting from Wave 1")
# ================================
# CAMERA GROUP
# ================================
class YsortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()
    
    #creating the floor
        self.floor_surf = pygame.image.load('graphics/tilemap/ground.png').convert()
        self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        #draw floor
        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf, floor_offset_pos)
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)

    def enemy_update(self, player):
        enemies = [s for s in self.sprites()
                   if hasattr(s, "sprite_type") and s.sprite_type == "enemy"]
        for enemy in enemies:
            enemy.enemy_update(player)
    
    