import pygame, sys
from menubutton import Button
pygame.init()
pygame.mixer.init()

bgmusic = pygame.mixer.Sound('./audio/melancholia.mp3')
bgmusic.play(loops = -1)

Screen = pygame.display.set_mode((1280,720))
pygame.display.set_caption("Wendigo")

def main_menu():
    while True:
        Screen.blit(pygame.image.load('./graphics/main_menu/main_menu.png').convert(), (0,0))

        Menu_MOUSE_POS = pygame.mouse.get_pos()

start_img = pygame.image.load('./graphics/main_menu/start.png').convert_alpha()
exit_img = pygame.image.load('./graphics/main_menu/exit.png').convert_alpha()

hover_sound = pygame.mixer.Sound('./audio/hover.mp3')
click_sound = pygame.mixer.Sound('./audio/click.mp3')

start_button = Button(490, 200, start_img, 0.5)
exit_button = Button(490, 400, exit_img, 0.5) 


run = True
while run: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    pygame.display.update()
    if start_button.draw(Screen) == True:
        bgmusic.stop()
        import test
        click_sound.play()
        test.Game().run()
    if exit_button.draw(Screen) == True:
        bgmusic.stop()
        click_sound.play()
        pygame.quit()
        sys.exit()
pygame.quit()