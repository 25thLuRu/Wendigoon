import pygame
pygame.mixer.init()

hover_sound = pygame.mixer.Sound('./audio/hover.mp3')
hover_sound.set_volume(0.2)
hover_sound_channel = pygame.mixer.Channel(1)
class Button:
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()

        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.hovered = False

        self.dark_image = self.image.copy()
        dark_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        dark_surface.fill((0, 0, 0, 100))  # RGBA, 100 is the alpha for darkness
        self.dark_image.blit(dark_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def draw(self, surface):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if not self.hovered:
                hover_sound_channel.play(hover_sound)
                self.hovered = True
                surface.blit(self.dark_image, (self.rect.x, self.rect.y))
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                self.clicked = True
                action = True
        else:
            self.hovered = False
            surface.blit(self.image, (self.rect.x, self.rect.y))
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        surface.blit(self.image, (self.rect.x, self.rect.y))
        return action