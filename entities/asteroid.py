# entities/asteroid.py
import pygame
import math
import random
from settings import *

class Asteroid:
    """Астероид — источник ресурсов"""
    
    def __init__(self, x, y, radius=None, health=None):
        self.x = x
        self.y = y
        self.radius = radius or random.randint(40, 120)
        self.health = health or self.radius // 10 + 2
        self.max_health = self.health
        
        # ===== ТИП РЕСУРСА =====
        self.resource_type = random.choices(
            ['scrap', 'crystal', 'fuel'],
            weights=[60, 20, 20]  # 60% скрап, 20% кристаллы, 20% топливо
        )[0]
        
        self.resource_amount = random.randint(5, 30) if self.resource_type == 'scrap' else random.randint(2, 10)
        
        # Физика
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.2, 0.8)
        self.speed_x = math.cos(angle) * speed
        self.speed_y = math.sin(angle) * speed
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        
        # Визуал
        self.color = (80 + random.randint(0, 40), 70 + random.randint(0, 30), 50 + random.randint(0, 20))
        self.vertices = self._generate_vertices()
        
        # Ресурсы при разрушении
        self.resource_amount = random.randint(5, 20)
    
    def _generate_vertices(self):
        """Генерирует неровный многоугольник для астероида"""
        num_vertices = random.randint(6, 10)
        vertices = []
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi
            # Неровность
            variation = 0.7 + random.random() * 0.6
            r = self.radius * variation
            vertices.append((r * math.cos(angle), r * math.sin(angle)))
        return vertices
    
    def update(self):
        """Обновление астероида"""
        self.x += self.speed_x
        self.y += self.speed_y
        self.rotation += self.rotation_speed
    
    def draw(self, screen, camera):
        """Рисует астероид с учётом зума"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        scaled_radius = self.radius * camera.zoom
        
        if screen_x < -scaled_radius - 50 or screen_x > WIDTH + scaled_radius + 50 or \
           screen_y < -scaled_radius - 50 or screen_y > HEIGHT + scaled_radius + 50:
            return
        
        # Повёрнутые вершины с учётом зума
        rot_rad = math.radians(self.rotation)
        cos_a = math.cos(rot_rad)
        sin_a = math.sin(rot_rad)
        
        rotated = []
        for vx, vy in self.vertices:
            rx = (vx * cos_a - vy * sin_a) * camera.zoom
            ry = (vx * sin_a + vy * cos_a) * camera.zoom
            rotated.append((screen_x + rx, screen_y + ry))
        
        # Рисуем
        pygame.draw.polygon(screen, self.color, rotated)
        pygame.draw.polygon(screen, (50, 50, 50), rotated, 1)
        
        # Полоса здоровья
        if self.max_health > 1:
            bar_width = int(30 * camera.zoom)
            bar_height = max(2, int(3 * camera.zoom))
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - scaled_radius - 8 * camera.zoom
            health_percent = self.health / self.max_health
            
            pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (200, 200, 50),
                            (bar_x, bar_y, bar_width * health_percent, bar_height))
     
    def take_damage(self, damage=1):
        """Получение урона"""
        self.health -= damage
        if self.health <= 0:
            return True  # Разрушен
        return False
    
    def destroy(self, particle_system=None):
        """Взрыв астероида"""
        if particle_system:
            particle_system.spawn_explosion(
                self.x, self.y,
                count=30,
                speed=4,
                colors=[(150, 130, 100), (100, 80, 60), (200, 180, 150)]
            )
            
        # Возвращаем тип ресурса и количество
        return {
            'type': self.resource_type,
            'amount': self.resource_amount
        }
        
    def get_vertices(self):
        """Возвращает вершины астероида для полигональной коллизии"""
        rot_rad = math.radians(self.rotation)
        cos_a = math.cos(rot_rad)
        sin_a = math.sin(rot_rad)
        
        vertices = []
        for vx, vy in self.vertices:
            rx = self.x + vx * cos_a - vy * sin_a
            ry = self.y + vx * sin_a + vy * cos_a
            vertices.append((rx, ry))
        return vertices