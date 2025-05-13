import pygame
import threading

pygame.init()
pygame.mixer.init()

def play_connect():
    sound = pygame.mixer.Sound('sounds/connect1.mp3')
    threading.Thread(target=sound.play, daemon=True).start()

def play_disconnect():
    sound = pygame.mixer.Sound('sounds/disconnect_discord.mp3')
    threading.Thread(target=sound.play, daemon=True).start()

def play_click():
    def wrapper(func):
        def inner(*args, **kwargs):
            sound = pygame.mixer.Sound('sounds/click3.mp3')
            threading.Thread(target=sound.play, daemon=True).start()
            return func(*args, **kwargs)
        return inner
    return wrapper