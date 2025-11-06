import pygame
from settings import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, damage, obstacles, owner="player"):
        super().__init__(groups)
        self.sprite_type = 'bullet'
        self.owner = owner  # 'player' or 'enemy'

        # Bullet color by owner
        if self.owner == "enemy":
            color = 'red'
        else:
            color = 'yellow'

        self.image = pygame.Surface((10, 5))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)

        # Use float position for smooth movement
        self.pos = pygame.math.Vector2(pos)

        # Normalize direction safely
        if direction.length_squared() > 0:
            self.direction = direction.normalize()
        else:
            self.direction = pygame.math.Vector2(0, -1)

        self.speed = 10
        self.damage = damage
        self.obstacles = obstacles

        # Move bullet slightly away from shooter so it doesn't collide immediately
        self.pos += self.direction * 20
        self.rect.center = self.pos

    def update(self):
        # Move bullet
        self.pos += self.direction * self.speed
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Destroy bullet if off-screen
        if (
            self.rect.right < 0 or self.rect.left > WIDTH or 
            self.rect.bottom < 0 or self.rect.top > HEIGHT
        ):
            self.kill()

        # Destroy if it hits any obstacle
        for obstacle in self.obstacles:
            if obstacle.rect.colliderect(self.rect):
                self.kill()
