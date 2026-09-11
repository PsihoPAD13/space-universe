# entities/ship.py
import math
import pygame
import random
from settings import (
    SHIP_ACCELERATION, SHIP_FRICTION, SHIP_MAX_SPEED,
    SHIP_ROTATION_SPEED, SHIP_RADIUS, SHIP_MAX_HEALTH,
    SHOOT_DELAY, WIDTH, HEIGHT,
    WHITE, BLUE, YELLOW, RED, GREEN
)
from entities.bullet import Bullet
from utils import draw_health_bar
from entities.weapon import Weapon

class Ship:
    def __init__(self, x, y, sprite_manager=None):
        self.x = x
        self.y = y
        self.angle = 0
        self.weapon_angle = 0
        self.speed_x = 0
        self.speed_y = 0
        self.radius = SHIP_RADIUS
        self.health = SHIP_MAX_HEALTH
        self.max_health = SHIP_MAX_HEALTH
        self.max_speed = SHIP_MAX_SPEED
        self.shield_active = False
        self.warp_multiplier = 1.0  # Множитель скорости (1 = норма, 5 = варп)
        self.normal_max_speed = SHIP_MAX_SPEED  # <-- Будет перезаписан в _apply_hull()
        self.warp_max_speed = SHIP_MAX_SPEED * 10
        
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY
        
        self.engine_on = False
        
        # Спрайт корабля
        self.sprite_manager = sprite_manager
        self.sprite = None
        self.current_hull = 'blade'
        self.current_weapon = 'blaster'
        self.current_engine = 'engine_small'
        self.current_shield = 'shield_basic'
        
        # ===== КАДРЫ КРЕНА =====
        self.rotation_frames = []
        self.current_frame = 0  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
        self.bank_angle = 0
        self.bank_decay = 0.95
    
        # Загружаем начальный корпус
        self._apply_hull(self.current_hull)
        
        self.max_speed = self.normal_max_speed
        
        # Оружие
        self.weapons = []
        self._init_weapons()
            
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY

    def aim_at(self, target_x, target_y):
        """Наводит оружие на цель"""
        dx = target_x - self.x
        dy = target_y - self.y
        
        if dx != 0 or dy != 0:
            self.weapon_angle = math.degrees(math.atan2(dy, dx))
    
    def update(self):
        # Применяем трение
        self.speed_x *= SHIP_FRICTION
        self.speed_y *= SHIP_FRICTION
        
        # Ограничиваем скорость
        speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if speed > self.max_speed:
            self.speed_x = (self.speed_x / speed) * self.max_speed
            self.speed_y = (self.speed_y / speed) * self.max_speed
        
        # Обновляем позицию
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Обновляем кулдаун стрельбы
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        # Возврат крена
        if self.bank_angle != 0:
            self.bank_angle *= self.bank_decay
            if abs(self.bank_angle) < 0.1:
                self.bank_angle = 0
            self.current_frame = abs(self.bank_angle)
        
    def rotate_left(self):
        self.angle -= SHIP_ROTATION_SPEED
        self.angle %= 360
        # Крен влево: bank_angle становится отрицательным
        self.bank_angle = max(self.bank_angle - 1, -15)
        self.current_frame = abs(self.bank_angle)  # Просто модуль!

    def rotate_right(self):
        self.angle += SHIP_ROTATION_SPEED
        self.angle %= 360
        # Крен вправо: bank_angle становится положительным
        self.bank_angle = min(self.bank_angle + 1, 15)
        self.current_frame = abs(self.bank_angle)  # Просто модуль!
    
    def _load_rotation_frames(self):
        """Загружает 16 кадров крена (только вправо)"""
        self.rotation_frames = []
        for i in range(16):
            frame = self.sprite_manager.get(f'{self.current_hull}_bank_{i}')
            if frame:
                self.rotation_frames.append(frame)
            else:
                # Заглушка
                self.rotation_frames.append(self.sprite_manager.get('player_base'))
            
    def thrust(self, has_fuel=True):
        """Тяга (только если есть топливо)"""
        if not has_fuel:
            self.engine_on = False
            return
        
        angle_rad = math.radians(self.angle)
        self.speed_x += math.cos(angle_rad) * SHIP_ACCELERATION
        self.speed_y += math.sin(angle_rad) * SHIP_ACCELERATION
        self.engine_on = True
    
    def stop_thrust(self):
        self.engine_on = False
    
    def _apply_hull(self, hull_id):
        """Применяет корпус из JSON"""
        if not self.sprite_manager:
            return
        
        data = self.sprite_manager.get_sprite_data('ships', hull_id)
        if not data:
            print(f"[SHIP] ⚠️ Корпус {hull_id} не найден")
            return
        
        # Загружаем кадры крена
        frames = self.sprite_manager.get(f"{hull_id}_bank_frames")
        if frames:
            self.rotation_frames = frames
            self.current_frame = 0
            print(f"[SHIP] {hull_id}: {len(frames)} кадров")
        
        # Размер
        size = data.get('size', [128, 128])
        self.radius = size[0] // 2
        self.current_hull = hull_id
        
        # Статы
        stats = data.get('stats', {})
        self.max_health = stats.get('hp', 100)
        self.health = self.max_health
        
        speed_multiplier = stats.get('speed', 1.0)
        self.normal_max_speed = SHIP_MAX_SPEED * speed_multiplier
        self.max_speed = self.normal_max_speed
        
        # Слоты (массив)
        self.hull_slots = self.sprite_manager.get_slots('ships', hull_id)
        
        print(f"[SHIP] HP: {self.max_health}, Speed: {self.normal_max_speed}, слотов: {len(self.hull_slots)}")     
        
    def _init_weapons(self):
        """Создаёт оружие из слотов корпуса"""
        self.weapons = []
        
        if not self.sprite_manager:
            return
        
        # Слоты — массив (новый формат)
        for slot in self.hull_slots:
            if slot.get('type') == 'weapon':
                weapon = Weapon(
                    self.current_weapon,
                    self.sprite_manager,
                    (slot['x'], slot['y']),
                    slot.get('z', 0.5)
                )
                self.weapons.append(weapon)
                print(f"[SHIP] Пушка в слот ({slot['x']}, {slot['y']}), z={slot.get('z', 0.5)}")    
    
    def set_weapon(self, weapon_id):
        """Меняет оружие на корабле"""
        self.current_weapon = weapon_id
        # Пересоздаём оружие
        self._init_weapons()    
    
    def aim_weapons(self, target_x, target_y):
        """Наводит всё оружие на цель"""
        for weapon in self.weapons:
            weapon.aim(target_x, target_y, self.x, self.y, self.angle)
    
    def shoot(self, bullets, target_world_x=None, target_world_y=None):
        """Стрельба из всех пушек"""
        if self.shoot_cooldown == 0:
            for weapon in self.weapons:
                weapon.shoot(
                    bullets, 
                    self.x, 
                    self.y, 
                    self.angle, 
                    self.speed_x, 
                    self.speed_y,
                    target_world_x,  # <-- передаём цель
                    target_world_y
                )
            self.shoot_cooldown = self.shoot_delay
            
    def draw(self, screen, camera, particle_system=None):
        """Рисует корабль с учётом зума"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        if screen_x < -200 or screen_x > WIDTH + 200 or \
           screen_y < -200 or screen_y > HEIGHT + 200:
            return
        
        # ===== КАДР КРЕНА =====
        frame = None
        if self.rotation_frames:
            frame_index = int(abs(self.bank_angle)) % len(self.rotation_frames)
            frame = self.rotation_frames[frame_index]
            
            if self.bank_angle < 0:
                frame = pygame.transform.flip(frame, False, True)
        
        if frame:
            # Масштабируем
            w = max(1, int(frame.get_width() * camera.zoom))
            h = max(1, int(frame.get_height() * camera.zoom))
            scaled = pygame.transform.scale(frame, (w, h))
            
            rotated = pygame.transform.rotate(scaled, -self.angle)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
        else:
            scaled_radius = max(1, int(self.radius * camera.zoom))
            pygame.draw.circle(screen, (255, 0, 255), (int(screen_x), int(screen_y)), scaled_radius)
        
        # ===== ОРУЖИЕ =====
        for weapon in self.weapons:
            weapon.draw(screen, camera, self.x, self.y, self.angle, self.bank_angle)
        
        # ===== ПЛАМЯ =====
        if self.engine_on and particle_system:
            angle_rad = math.radians(self.angle)
            flame_angle = angle_rad + math.radians(180)
            flame_x = self.x + math.cos(flame_angle) * self.radius
            flame_y = self.y + math.sin(flame_angle) * self.radius
            
            particle_system.spawn_spark_trail(flame_x, flame_y, (255, 150, 50), speed=3, count=3)
            particle_system.spawn_smoke_trail(flame_x, flame_y, count=2, speed=1)
        
        # ===== ЩИТ =====
        if self.shield_active:
            shield_radius = int((self.radius + 10) * camera.zoom)
            shield_alpha = 50 + 30 * math.sin(pygame.time.get_ticks() * 0.005)
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shield_color = (50, 150, 255, int(shield_alpha))
            pygame.draw.circle(shield_surf, shield_color, (shield_radius, shield_radius), shield_radius, 3)
            screen.blit(shield_surf, (int(screen_x - shield_radius), int(screen_y - shield_radius)))
        
        # ===== HP =====
        draw_health_bar(screen, screen_x, screen_y - self.radius * camera.zoom - 10,
                       self.health, self.max_health,
                       width=int(40 * camera.zoom), height=max(2, int(5 * camera.zoom)))
        
    def set_warp(self, active):
        if active:
            self.warp_multiplier = 10.0
            self.max_speed = self.warp_max_speed
        else:
            self.warp_multiplier = 1.0
            self.max_speed = self.normal_max_speed    
            
    def is_warping(self):
        return self.warp_multiplier > 1.0
        
    def get_vertices(self):
        """Возвращает вершины корабля для полигональной коллизии"""
        angle_rad = math.radians(self.angle)
        
        # Нос
        nose_x = self.x + math.cos(angle_rad) * self.radius
        nose_y = self.y + math.sin(angle_rad) * self.radius
        
        # Левый и правый борта
        left_angle = angle_rad + math.radians(140)
        right_angle = angle_rad - math.radians(140)
        
        left_x = self.x + math.cos(left_angle) * self.radius
        left_y = self.y + math.sin(left_angle) * self.radius
        right_x = self.x + math.cos(right_angle) * self.radius
        right_y = self.y + math.sin(right_angle) * self.radius
        
        return [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
    
    def get_collision_radius(self):
        """Возвращает радиус коллизии (с учетом щита)"""
        if self.shield_active:
            return self.radius + 10
        return self.radius

    def update_speed(self):
        """Принудительно обновляет текущую скорость"""
        if self.is_warping():
            self.max_speed = self.warp_max_speed
        else:
            self.max_speed = self.normal_max_speed
        print(f"[SHIP] Speed updated: {self.max_speed}")
        
    def _update_bank_frame(self):
        """Обновляет кадр крена на основе bank_angle (-15..15)"""
        # bank_angle: -15 (влево) ... 0 (центр) ... 15 (вправо)
        # Преобразуем в индекс кадра: 0..15
        # 0 = центр, 1-7 = крен вправо, 8-15 = крен влево
        if self.bank_angle >= 0:
            # Крен вправо: 0 → 0, 1 → 1, 15 → 15
            self.current_frame = self.bank_angle
        else:
            # Крен влево: -1 → 15, -15 → 1
            self.current_frame = 16 + self.bank_angle  # 16 + (-1) = 15, 16 + (-15) = 1
        
        # Ограничиваем
        self.current_frame = max(0, min(15, self.current_frame))