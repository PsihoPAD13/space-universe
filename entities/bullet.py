# entities/bullet.py
import pygame
from settings import BULLET_RADIUS, BULLET_LIFE, YELLOW, WIDTH, HEIGHT

class Bullet:
    def __init__(self, x, y, speed_x, speed_y):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.radius = BULLET_RADIUS
        self.life = BULLET_LIFE
        self.damage = 10
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
    
    def draw(self, screen, camera):
        """Рисует пулю с учётом зума"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        scaled_radius = max(1, int(self.radius * camera.zoom))
        
        if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
            pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), scaled_radius)
            pygame.draw.circle(screen, (255, 255, 100), 
                             (int(screen_x), int(screen_y)), scaled_radius + 1, 1)
    
    def is_dead(self):
        return self.life <= 0