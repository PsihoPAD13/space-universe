# entities/enemy.py
import math
import random
import pygame
from settings import *
from entities.bullet import Bullet
from utils import draw_health_bar, distance


class Enemy:
    def __init__(self, x, y, enemy_type='scout', sprite_manager=None, 
             difficulty_multiplier=1.0, base_color=None):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.sprite_manager = sprite_manager
        
        # ===== ЗАГРУЖАЕМ ДАННЫЕ ИЗ JSON =====
        data = None
        if sprite_manager:
            data = sprite_manager.get_sprite_data('enemies', enemy_type)
        
        if not data:
            # Fallback
            data = {
                'size': [64, 64],
                'stats': {'hp': 2, 'speed': 3.0, 'behavior': 'chase', 'score': 10}
            }
        
        stats = data.get('stats', {})
        
        # ===== СТАТЫ =====
        self.radius = data.get('size', [64, 64])[0] // 2
        self.health = int(stats.get('hp', 2) * difficulty_multiplier)
        self.max_health = self.health
        self.speed = stats.get('speed', 3.0)
        self.behavior = stats.get('behavior', 'chase')
        self.score_value = stats.get('score', 10)
        
        # Стрельба (по умолчанию)
        self.can_shoot = stats.get('can_shoot', True)
        self.shoot_delay = stats.get('shoot_delay', 60)
        self.bullet_speed = stats.get('bullet_speed', 5)
        self.bullet_type = stats.get('bullet_type', 'forward')
        self.shoot_cooldown = random.randint(0, self.shoot_delay)
        
        # ===== ЦВЕТ (ОТ БАЗЫ) =====
        if base_color is None:
            base_color = (255, 255, 255)  # Белый по умолчанию
        self.color = base_color
    
        # ===== КАДРЫ КРЕНА С ЦВЕТОМ =====
        self.rotation_frames = []
        self.current_frame = 0
        self.bank_angle = 0
        self.prev_angle = 0  # <-- ДОБАВИТЬ
        if sprite_manager:
            # Получаем перекрашенные кадры
            colored_frames = sprite_manager.get_colored_frames(enemy_type, base_color)
            if colored_frames:
                self.rotation_frames = colored_frames
                print(f"[ENEMY] {enemy_type}: {len(colored_frames)} кадров, цвет {base_color}")
            else:
                # Fallback — оригинальные кадры
                frames = sprite_manager.get(f"{enemy_type}_bank_frames")
                if frames:
                    self.rotation_frames = frames
                
        # ===== ФИЗИКА =====
        angle = random.uniform(0, 2 * math.pi)
        self.speed_x = math.cos(angle) * self.speed * 0.5
        self.speed_y = math.sin(angle) * self.speed * 0.5
        
        # Для орбиты
        self.orbit_angle = random.uniform(0, 2 * math.pi)
        self.orbit_radius = random.randint(100, 200)
        
        # Для камикадзе
        self.explosion_radius = 80
        self.is_exploding = False
        
        # Для стационарных
        self.shoot_timer = 0
    
    def update(self, player_x, player_y):
        """Обновление врага"""
        # Поведение
        if self.behavior == 'chase':
            self._update_chase(player_x, player_y)
        elif self.behavior == 'stationary':
            self._update_stationary(player_x, player_y)
        elif self.behavior == 'kamikaze':
            self._update_kamikaze(player_x, player_y)
        elif self.behavior == 'orbit':
            self._update_orbit(player_x, player_y)
        
        # Кулдаун стрельбы
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        # ===== АНИМАЦИЯ КРЕНА =====
        current_angle = math.degrees(math.atan2(self.speed_y, self.speed_x))
        angle_diff = current_angle - self.prev_angle

        # Нормализуем разницу (-180..180)
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        # Крен от резкого поворота
        self.bank_angle += angle_diff * 0.5
        self.bank_angle = max(-15, min(15, self.bank_angle))

        # Затухание
        self.bank_angle *= 0.99
        if abs(self.bank_angle) < 0.1:
            self.bank_angle = 0

        self.prev_angle = current_angle
        self.current_frame = int(abs(self.bank_angle))            
    
    def _update_chase(self, player_x, player_y):
        """Преследование игрока"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            acceleration = 0.05 + 0.02 * (dist / 500)
            self.speed_x += (dx / dist) * min(acceleration, 0.1)
            self.speed_y += (dy / dist) * min(acceleration, 0.1)
            
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
    
    def _update_stationary(self, player_x, player_y):
        """Стоит на месте"""
        self.x += self.speed_x * 0.02
        self.y += self.speed_y * 0.02
        
        # Телепорт если далеко
        dx = player_x - self.x
        dy = player_y - self.y
        if math.sqrt(dx**2 + dy**2) > 600:
            self.x = player_x + dx * 0.3
            self.y = player_y + dy * 0.3
    
    def _update_kamikaze(self, player_x, player_y):
        """Летит к игроку и взрывается"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            acceleration = 0.1
            self.speed_x += (dx / dist) * acceleration
            self.speed_y += (dy / dist) * acceleration
            
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
        
        if dist < self.explosion_radius and not self.is_exploding:
            self.is_exploding = True
    
    def _update_orbit(self, player_x, player_y):
        """Кружится вокруг игрока"""
        self.orbit_angle += 0.015
        
        target_x = player_x + math.cos(self.orbit_angle) * self.orbit_radius
        target_y = player_y + math.sin(self.orbit_angle) * self.orbit_radius
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            self.speed_x += (dx / dist) * 0.05
            self.speed_y += (dy / dist) * 0.05
            
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
                
    def shoot(self, enemy_bullets, player_x, player_y):
        if not self.can_shoot:
            return
        
        if self.shoot_cooldown > 0:
            return
        
        if self.behavior == 'kamikaze':
            return
        
        self.shoot_cooldown = self.shoot_delay
        
        # Угол спрайта
        sprite_rad = math.atan2(self.speed_y, self.speed_x)
        
        # Позиция дула
        barrel_length = self.radius
        bullet_x = self.x + math.cos(sprite_rad) * barrel_length
        bullet_y = self.y + math.sin(sprite_rad) * barrel_length
        
        # ===== ТИП ПУЛИ =====
        if self.bullet_type == 'forward':
            # Летит вперёд (по направлению спрайта)
            speed_x = math.cos(sprite_rad) * self.bullet_speed
            speed_y = math.sin(sprite_rad) * self.bullet_speed
        else:  # target
            # Летит на игрока
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                speed_x = (dx / dist) * self.bullet_speed
                speed_y = (dy / dist) * self.bullet_speed
            else:
                return
        
        enemy_bullets.append(Bullet(bullet_x, bullet_y, speed_x, speed_y))
    
    def draw(self, screen, camera, player_x=0, player_y=0):
        """Рисует врага с учётом зума"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        if screen_x < -200 or screen_x > WIDTH + 200 or \
           screen_y < -200 or screen_y > HEIGHT + 200:
            return
        
        # Спрайт с креном
        if self.rotation_frames:
            frame_index = int(abs(self.bank_angle)) % len(self.rotation_frames)
            frame = self.rotation_frames[frame_index]
            
            if self.bank_angle < 0:
                frame = pygame.transform.flip(frame, False, True)
            
            # Поворот по движению
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            angle = math.degrees(math.atan2(self.speed_y, self.speed_x)) if speed > 0.5 else 0
            
            # Масштабируем
            w = max(1, int(frame.get_width() * camera.zoom))
            h = max(1, int(frame.get_height() * camera.zoom))
            scaled = pygame.transform.scale(frame, (w, h))
            
            rotated = pygame.transform.rotate(scaled, -angle)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
        else:
            scaled_radius = max(1, int(self.radius * camera.zoom))
            pygame.draw.circle(screen, (255, 0, 255), (int(screen_x), int(screen_y)), scaled_radius)
        
        # Полоса здоровья
        if self.max_health > 1:
            draw_health_bar(screen, screen_x, screen_y - self.radius * camera.zoom - 8,
                           self.health, self.max_health,
                           width=int(30 * camera.zoom), height=max(2, int(5 * camera.zoom)))
        
        # Взрыв камикадзе
        if self.is_exploding:
            pygame.draw.circle(screen, (255, 200, 50),
                             (int(screen_x), int(screen_y)),
                             int(self.explosion_radius * camera.zoom), 3)  
                             
    def take_damage(self, damage=1):
        self.health -= damage
        return self.health <= 0
    
    def destroy(self, particle_system):
        """Взрыв"""
        if particle_system:
            particle_system.spawn_explosion(
                self.x, self.y,
                count=20,
                speed=5,
                colors=[(255, 100, 50), (255, 200, 50), (255, 255, 255)]
            )