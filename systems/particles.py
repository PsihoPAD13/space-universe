# particles.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT

class Particle:
    """Отдельная частица"""
    def __init__(self, x, y, dx, dy, size, color, lifetime, gravity=0, friction=0.98):
        self.x = x
        self.y = y
        self.dx = dx  # Скорость по X
        self.dy = dy  # Скорость по Y
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.friction = friction
        self.alive = True
        
        # Эффект затухания размера
        self.start_size = size
    
    def update(self):
        # Движение
        self.dx *= self.friction
        self.dy *= self.friction
        self.dy += self.gravity  # Гравитация (для реалистичности)
        
        self.x += self.dx
        self.y += self.dy
        
        # Уменьшаем время жизни
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
        
        # Уменьшаем размер при старении
        life_ratio = self.lifetime / self.max_lifetime
        self.size = self.start_size * life_ratio
        if self.size < 0.5:
            self.size = 0.5
    
    def draw(self, screen, camera):
        if not self.alive:
            return
        
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        size = max(1, int(self.size * camera.zoom))
        
        if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
            pygame.draw.circle(surf, color_with_alpha, (size, size), size)
            
            if self.color[0] > 200 or self.color[1] > 200 or self.color[2] > 200:
                pygame.draw.circle(surf, (255, 255, 255, alpha // 3), (size, size), size // 3)
            
            screen.blit(surf, (int(screen_x - size), int(screen_y - size)))

class ParticleSystem:
    """Система частиц"""
    def __init__(self):
        self.particles = []
    
    def spawn_explosion(self, x, y, count=30, speed=5, colors=None):
        """Создает взрыв"""
        if colors is None:
            colors = [
                (255, 200, 50),  # Желтый
                (255, 150, 50),  # Оранжевый
                (255, 100, 50),  # Оранжево-красный
                (255, 50, 50),   # Красный
                (255, 255, 200), # Белый
            ]
        
        for _ in range(count):
            # Случайное направление
            angle = random.uniform(0, 2 * math.pi)
            speed_mult = random.uniform(0.3, 1.0)
            speed_x = math.cos(angle) * speed * speed_mult
            speed_y = math.sin(angle) * speed * speed_mult
            
            size = random.uniform(2, 6)
            lifetime = random.randint(15, 40)
            color = random.choice(colors)
            
            self.particles.append(Particle(
                x, y, speed_x, speed_y,
                size, color, lifetime,
                gravity=0.05,
                friction=0.98
            ))
        
        # Добавляем искры (быстрые, яркие, маленькие)
        for _ in range(count // 2):
            angle = random.uniform(0, 2 * math.pi)
            speed_mult = random.uniform(0.5, 1.5)
            speed_x = math.cos(angle) * speed * 1.5 * speed_mult
            speed_y = math.sin(angle) * speed * 1.5 * speed_mult
            
            self.particles.append(Particle(
                x, y, speed_x, speed_y,
                random.uniform(1, 3),
                (255, 255, 255),
                random.randint(10, 25),
                gravity=0.02,
                friction=0.95
            ))
    
    def spawn_smoke_trail(self, x, y, count=10, speed=1):
        """Создает дымный след (для двигателя)"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed_mult = random.uniform(0.2, 0.8)
            speed_x = math.cos(angle) * speed * speed_mult
            speed_y = math.sin(angle) * speed * speed_mult
            
            size = random.uniform(3, 8)
            lifetime = random.randint(10, 30)
            brightness = random.randint(100, 200)
            color = (brightness, brightness, brightness)
            
            self.particles.append(Particle(
                x, y, speed_x, speed_y,
                size, color, lifetime,
                gravity=0.01,
                friction=0.99
            ))
    
    def spawn_spark_trail(self, x, y, color, speed=2, count=3):
        """Создает искры (для двигателя)"""
        for _ in range(count):
            angle = random.uniform(-math.pi/2, math.pi/2)  # Только назад
            speed_mult = random.uniform(0.5, 1.5)
            speed_x = math.cos(angle + math.pi) * speed * speed_mult
            speed_y = math.sin(angle + math.pi) * speed * speed_mult
            
            self.particles.append(Particle(
                x, y, speed_x, speed_y,
                random.uniform(1, 3),
                color,
                random.randint(5, 15),
                gravity=0.0,
                friction=0.92
            ))
    
    def update(self):
        """Обновляет все частицы"""
        for particle in self.particles[:]:
            particle.update()
            if not particle.alive:
                self.particles.remove(particle)
    
    def draw(self, screen, camera):
        for particle in self.particles:
            particle.draw(screen, camera)
    
    def clear(self):
        """Очищает все частицы"""
        self.particles.clear()