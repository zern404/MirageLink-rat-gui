import pygame

pygame.init()
pygame.mixer.init()

def connect():
    sound = pygame.mixer.Sound('sounds/connect1.mp3').play()

def disconnect():
    sound = pygame.mixer.Sound('sounds/disconnect_discord.mp3').play()

def click():
    sound = pygame.mixer.Sound('sounds/click3.mp3').play()