import pygame
from settings import *

class UI:
    def __init__(self):
        #general setup
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(UI_FONT, UI_FONT_SIZE)
        #bar setup
        self.health_bar_rect = pygame.Rect(10, 10, HEALTH_BAR_WIDTH, BAR_HEIGHT)
        self.energy_bar_rect = pygame.Rect(10, 50, ENERGY_BAR_WIDTH, BAR_HEIGHT)

        #weapon dictionary
        self.item_graphics = []
        for settings in item_data.values():
            path = settings['graphic']
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(image, (64, 64))
            self.item_graphics.append(image)

        icon_path = './graphics/ui/bullet.png'
        try:
            icon_surf = pygame.image.load(icon_path).convert_alpha()
            icon_size = int(self.font.get_height() * 1.2)
            self.bullet_icon = pygame.transform.scale(icon_surf, (icon_size, icon_size))
        except Exception:
            self.bullet_icon = None
    
    def show_bar(self, current, max_amount, bg_rect, color):
        #draw bg
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)
        #converting stat to pixel
        ratio = current / max_amount
        current_width = bg_rect.width * ratio
        current_rect = bg_rect.copy()
        current_rect.width = current_width

        #drawing the bar
        pygame.draw.rect(self.display_surface, color, current_rect)
        pygame.draw.rect(self.display_surface, 'gold', bg_rect, 3)
    
    def show_ammo(self, ammo):
        text_surf = self.font.render(str(ammo), False, BULLET_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = self.display_surface.get_size()[1] - 20
        text_rect = text_surf.get_rect(bottomright = (x, y))

        padding = 7
        if getattr(self, 'bullet_icon', None):
            icon_rect = self.bullet_icon.get_rect()
            icon_rect.bottomright = (text_rect.left - padding, y)
            # background covers both icon and text
            bg_rect = text_rect.union(icon_rect).inflate(20, 20)
            # draw background
            pygame.draw.rect(self.display_surface, '#3b3b3b', bg_rect)
            self.display_surface.blit(self.bullet_icon, icon_rect)
            self.display_surface.blit(text_surf, text_rect)
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        else:
            # fallback: existing behavior
            pygame.draw.rect(self.display_surface, '#3b3b3b', text_rect.inflate(20,20))
            self.display_surface.blit(text_surf, text_rect)
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, text_rect.inflate(20,20),3)

    def select_box(self, left, top, has_switched):
        bg_rect = pygame.Rect(left, top, ITEM_BOX_SIZE, ITEM_BOX_SIZE)
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)
        if has_switched:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        else:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR_ACTIVE, bg_rect, 3)
        return bg_rect
    
    def item_overlay(self, item_index, has_switched, cooldown_ratio=0):
        # 0 = no cooldown and 1 = cooldown
        bg_rect = self.select_box(30, 600, has_switched)
        item_surf = self.item_graphics[item_index]
        item_rect = item_surf.get_rect(center=bg_rect.center)

        # draw the item
        self.display_surface.blit(item_surf, item_rect)

        # draw cooldown overlay if needed
        if cooldown_ratio > 0:
            overlay = pygame.Surface(item_rect.size).convert_alpha()
            overlay.fill((255, 255, 255, int(180 * cooldown_ratio)))  # white, semi-transparent
            self.display_surface.blit(overlay, item_rect.topleft)

    def display(self, player):
        self.show_bar(player.health, player.stats['health'], self.health_bar_rect, HEALTH_COLOR)
        self.show_bar(player.sprint_energy, player.stats['sprint_energy'], self.energy_bar_rect, ENERGY_COLOR)
        self.show_ammo(player.ammo)
        self.item_overlay(player.item_index,player.can_switch)