# entities/player_base.py
import pygame
import math
from settings import *

class PlayerBase:
    """База игрока — точка восстановления и апгрейдов"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 80
        self.health = 200
        self.max_health = 200
        self.alive = True
        
        # Восстановление
        self.repair_rate = 1  # HP за тик
        self.repair_cooldown = 0
        self.repair_delay = 30  # Кадров между восстановлением
        
        # Апгрейды
        self.upgrades = {
            'repair_speed': 1,   # Уровень восстановления
            'shield_power': 0,   # Мощность щита базы
            'turret_count': 0,   # Количество турелей
            'storage': 0,        # Вместимость ресурсов
        }
        
        # Ресурсы
        self.resources = {
            'scrap': 0,
            'crystal': 0,
            'fuel': 0,
        }
        
        # Визуальные эффекты
        self.pulse = 0
        self.glow_radius = self.radius
    
    def update(self, ship, particle_system=None):
        """Обновление базы"""
        self.pulse += 0.02
        self.glow_radius = self.radius + 5 * math.sin(self.pulse)
        
        # Восстановление HP корабля
        if self.repair_cooldown <= 0:
            if ship.health < ship.max_health:
                ship.health = min(ship.max_health, ship.health + self.repair_rate)
                self.repair_cooldown = self.repair_delay
                
                # Эффект восстановления
                if particle_system:
                    particle_system.spawn_explosion(
                        ship.x, ship.y,
                        count=3,
                        speed=1,
                        colors=[(50, 255, 50), (255, 255, 255)]
                    )
        else:
            self.repair_cooldown -= 1
        
        # Эффект восстановления вокруг базы
        if particle_system and self.repair_cooldown == 0:
            angle = math.radians(pygame.time.get_ticks() * 0.05 % 360)
            px = self.x + math.cos(angle) * (self.radius + 20)
            py = self.y + math.sin(angle) * (self.radius + 20)
            particle_system.spawn_spark_trail(
                px, py,
                (50, 255, 100),
                speed=1,
                count=1
            )
        
    def draw(self, screen, camera):
        """Рисует базу игрока с учётом зума"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        scaled_radius = int(self.radius * camera.zoom)
        
        if screen_x < -200 or screen_x > WIDTH + 200 or \
           screen_y < -200 or screen_y > HEIGHT + 200:
            return
        
        glow_size = int(self.glow_radius * 2.5 * camera.zoom)
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (50, 200, 255, 30), (glow_size, glow_size), glow_size)
        screen.blit(glow, (int(screen_x - glow_size), int(screen_y - glow_size)))
        
        # Внешнее кольцо
        pygame.draw.circle(screen, (50, 150, 255), (int(screen_x), int(screen_y)),
                         int(self.glow_radius * camera.zoom), 2)
        
        # Внутреннее кольцо
        pygame.draw.circle(screen, (100, 200, 255), (int(screen_x), int(screen_y)),
                         int(self.radius * 0.8 * camera.zoom), 2)
        
        # Центр
        pygame.draw.circle(screen, (50, 150, 255), (int(screen_x), int(screen_y)),
                         max(3, int(10 * camera.zoom)))
        
        # Крест
        size = int(15 * camera.zoom)
        pygame.draw.line(screen, (150, 220, 255),
                       (int(screen_x - size), int(screen_y)),
                       (int(screen_x + size), int(screen_y)), 2)
        pygame.draw.line(screen, (150, 220, 255),
                       (int(screen_x), int(screen_y - size)),
                       (int(screen_x), int(screen_y + size)), 2)
        
        # HP бар
        bar_width = int(50 * camera.zoom)
        bar_height = max(2, int(4 * camera.zoom))
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - scaled_radius - 15
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 50),
                        (bar_x, bar_y, bar_width * health_percent, bar_height))    
        
    def is_near(self, x, y, radius=100):
        """Проверка, находится ли точка рядом с базой"""
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx**2 + dy**2) < radius
    
    def take_damage(self, damage):
        """Получение урона"""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True
        return False