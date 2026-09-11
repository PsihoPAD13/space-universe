# entities/weapon.py
import pygame
import math
from settings import *


class Weapon:
    def __init__(self, weapon_id, sprite_manager, slot_offset=(0, 0), slot_z=0.5):
        self.weapon_id = weapon_id
        self.sprite_manager = sprite_manager
        self.slot_offset = slot_offset
        self.slot_z = slot_z
        
        self.data = sprite_manager.get_sprite_data('weapons', weapon_id)
        if not self.data:
            self.data = {'type': 'static', 'stats': {'damage': 10, 'fire_rate': 0.3}}
        
        self.weapon_type = self.data.get('type', 'static')
        
        # ===== ЗАГРУЖАЕМ КАДРЫ КРЕНА =====
        self.rotation_frames = []
        frames = sprite_manager.get(f"{weapon_id}_bank_frames")
        if frames:
            self.rotation_frames = frames
        
        self.current_frame = 0
        self.bank_angle = 0
        self.prev_angle = 0
        
        self.pivot = self.data.get('pivot', [8, 8])
        self.angle = 0
        
        stats = self.data.get('stats', {})
        self.damage = stats.get('damage', 10)
        self.fire_rate = stats.get('fire_rate', 0.3)
        self.shoot_delay = int(60 * self.fire_rate)
        
    def aim(self, target_x, target_y, ship_x, ship_y, ship_angle=0):
        """Наводит оружие на цель (для турелей)"""
        if self.weapon_type == 'turret':
            dx = target_x - (ship_x + self.slot_offset[0])
            dy = target_y - (ship_y + self.slot_offset[1])
            self.angle = math.degrees(math.atan2(dy, dx))
        else:
            self.angle = ship_angle
    
    def draw(self, screen, camera, ship_x, ship_y, ship_angle, ship_bank_angle=0):
        """Рисует оружие с учётом поворота, крена и зума"""
        
        # ===== 1. ЛОКАЛЬНЫЕ КООРДИНАТЫ =====
        local_x = self.slot_offset[0]
        local_y = self.slot_offset[1]
        
        # ===== 2. СМЕЩЕНИЕ ОТ КРЕНА (в локальной системе) =====
        bank_rad = math.radians(ship_bank_angle * 4)
        dist = abs(local_x)
        
        # Смещение к центру (по локальной X)
        x_shift = dist * (1 - math.cos(bank_rad)) * self.slot_z * 0.5
        if local_x > 0:
            local_x -= x_shift
        else:
            local_x += x_shift
        
        # Смещение по Y (вверх/вниз)
        y_shift = dist * math.sin(bank_rad) * self.slot_z
        if ship_bank_angle > 0:
            local_y -= y_shift
        else:
            local_y += y_shift
        
        # ===== 3. ПОВОРОТ НА УГОЛ КОРАБЛЯ =====
        angle_rad = math.radians(ship_angle)
        offset_x = local_x * math.cos(angle_rad) - local_y * math.sin(angle_rad)
        offset_y = local_x * math.sin(angle_rad) + local_y * math.cos(angle_rad)
        
        # ===== 4. МИРОВЫЕ КООРДИНАТЫ =====
        world_x = ship_x + offset_x
        world_y = ship_y + offset_y
        
        # ===== 5. ЭКРАННЫЕ КООРДИНАТЫ =====
        screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        
        if screen_x < -50 or screen_x > WIDTH + 50 or \
           screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        # ===== 6. ОТРИСОВКА =====
        if self.rotation_frames:
            # Выбираем кадр по крену
            frame_index = int(abs(ship_bank_angle)) % len(self.rotation_frames)
            frame = self.rotation_frames[frame_index]
            
            # Зеркалим при крене влево
            if ship_bank_angle < 0:
                frame = pygame.transform.flip(frame, False, True)
            
            # Поворачиваем на угол
            if self.weapon_type == 'static':
                draw_angle = ship_angle
            else:
                draw_angle = self.angle
            
            # Масштабируем
            w = max(1, int(frame.get_width() * camera.zoom))
            h = max(1, int(frame.get_height() * camera.zoom))
            scaled = pygame.transform.scale(frame, (w, h))
            
            rotated = pygame.transform.rotate(scaled, -draw_angle - 90)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
        
    def shoot(self, bullets, ship_x, ship_y, ship_angle, ship_speed_x=0, ship_speed_y=0,
              target_world_x=None, target_world_y=None):
        """Стрельба из пушки с учётом крена и цели"""
        
        # ===== 1. ЛОКАЛЬНЫЕ КООРДИНАТЫ =====
        local_x = self.slot_offset[0]
        local_y = self.slot_offset[1]
        
        # ===== 2. ПОВОРОТ НА УГОЛ КОРАБЛЯ =====
        ship_angle_rad = math.radians(ship_angle)
        offset_x = local_x * math.cos(ship_angle_rad) - local_y * math.sin(ship_angle_rad)
        offset_y = local_x * math.sin(ship_angle_rad) + local_y * math.cos(ship_angle_rad)
        
        # ===== 3. ПОЗИЦИЯ ПУШКИ В МИРЕ =====
        gun_x = ship_x + offset_x
        gun_y = ship_y + offset_y
        
        # ===== 4. ОПРЕДЕЛЯЕМ НАПРАВЛЕНИЕ =====
        if self.weapon_type == 'turret' and target_world_x is not None and target_world_y is not None:
            # Турель — летит в цель (мышку)
            dx = target_world_x - gun_x
            dy = target_world_y - gun_y
        else:
            # Статичная — летит вперёд
            angle_rad = math.radians(ship_angle)
            dx = math.cos(angle_rad)
            dy = math.sin(angle_rad)
        
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return
        
        # ===== 5. СОЗДАЁМ ПУЛЮ =====
        bullet_speed = 10
        
        # Направление + скорость корабля
        speed_x = (dx / dist) * bullet_speed + ship_speed_x * 0.3
        speed_y = (dy / dist) * bullet_speed + ship_speed_y * 0.3
        
        from entities.bullet import Bullet
        bullet = Bullet(gun_x, gun_y, speed_x, speed_y)
        bullet.damage = self.damage
        bullets.append(bullet)