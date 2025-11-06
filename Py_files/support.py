import os
from csv import reader
from os import walk
import pygame


def import_csv_layout(path):
    # make path absolute relative to this file
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(base_path, path)
    
    terrain_map = []
    with open(full_path) as level_map:
        layout = reader(level_map, delimiter=',')
        for row in layout:
            terrain_map.append(list(row))
    return terrain_map




def import_folder(path, scale=None):
    surface_list = []
    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()

            # ⬇️ Scale if needed
            if scale:
                image_surf = pygame.transform.scale(image_surf, scale)

            surface_list.append(image_surf)

    if not surface_list:
        print(f"⚠️ No images found in: {path}")
    return surface_list