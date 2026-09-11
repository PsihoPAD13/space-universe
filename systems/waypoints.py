# systems/waypoints.py
import pygame
import math
from settings import WIDTH, HEIGHT

class Waypoint:
    """Маркер на карте и в игре"""
    
    def __init__(self, x, y, label="Marker"):
        self.x = x
        self.y = y
        self.label = label
        self.active = True
        self.color = (0, 200, 255)  # Голубой
        self.size = 10
    
    def draw_on_map(self, screen, world_to_screen, is_visible):
        """Рисует маркер на большой карте"""
        if not self.active:
            return
        
        if is_visible(self.x, self.y):
            sx, sy = world_to_screen(self.x, self.y)
            
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                # Круг с крестом
                pygame.draw.circle(screen, self.color, (int(sx), int(sy)), 8, 2)
                pygame.draw.line(screen, self.color, (sx - 5, sy), (sx + 5, sy), 2)
                pygame.draw.line(screen, self.color, (sx, sy - 5), (sx, sy + 5), 2)
                
                # Подпись
                font = pygame.font.Font(None, 16)
                label = font.render(self.label, True, self.color)
                screen.blit(label, (sx + 12, sy - 8))
    
    def draw_in_game(self, screen, player_x, player_y, camera_x, camera_y):
        """Рисует указатель на маркер в игре"""
        if not self.active:
            return
        
        # Проверяем, виден ли маркер на экране
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Если маркер виден - рисуем его
        if -20 < screen_x < WIDTH + 20 and -20 < screen_y < HEIGHT + 20:
            # Круг с крестом на игровом поле
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), 12, 2)
            pygame.draw.line(screen, self.color, (screen_x - 8, screen_y), (screen_x + 8, screen_y), 2)
            pygame.draw.line(screen, self.color, (screen_x, screen_y - 8), (screen_x, screen_y + 8), 2)
            
            # Расстояние до маркера
            dist = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
            font = pygame.font.Font(None, 14)
            dist_text = font.render(f"{int(dist)}m", True, (150, 150, 150))
            screen.blit(dist_text, (screen_x - 15, screen_y + 18))
            
            # Подпись
            font_big = pygame.font.Font(None, 16)
            label = font_big.render(self.label, True, self.color)
            screen.blit(label, (screen_x - 20, screen_y - 30))
        
        else:
            # Маркер за пределами экрана - показываем стрелку на границе
            dx = self.x - player_x
            dy = self.y - player_y
            angle = math.atan2(dy, dx)
            
            # Вычисляем позицию на краю экрана
            margin = 60
            cx = WIDTH // 2
            cy = HEIGHT // 2
            
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            t_values = []
            if cos_a > 0:
                t_values.append((WIDTH - margin - cx) / cos_a)
            elif cos_a < 0:
                t_values.append((margin - cx) / cos_a)
            
            if sin_a > 0:
                t_values.append((HEIGHT - margin - cy) / sin_a)
            elif sin_a < 0:
                t_values.append((margin - cy) / sin_a)
            
            t = min([t for t in t_values if t > 0])
            
            px = cx + t * cos_a
            py = cy + t * sin_a
            
            # Рисуем стрелку-указатель
            size = 15
            tip_x = px + math.cos(angle) * size
            tip_y = py + math.sin(angle) * size
            
            left_angle = angle + math.pi * 0.7
            right_angle = angle - math.pi * 0.7
            
            left_x = px + math.cos(left_angle) * size * 0.6
            left_y = py + math.sin(left_angle) * size * 0.6
            right_x = px + math.cos(right_angle) * size * 0.6
            right_y = py + math.sin(right_angle) * size * 0.6
            
            points = [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 1)
            
            # Подпись у стрелки
            font = pygame.font.Font(None, 14)
            label = font.render(self.label, True, self.color)
            label_x = px + math.cos(angle + math.pi * 0.3) * size * 1.5
            label_y = py + math.sin(angle + math.pi * 0.3) * size * 1.5
            screen.blit(label, (label_x - 15, label_y - 8))
            
            # Расстояние
            dist = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
            font_small = pygame.font.Font(None, 12)
            dist_text = font_small.render(f"{int(dist)}m", True, (150, 150, 150))
            dist_x = px + math.cos(angle - math.pi * 0.3) * size * 1.5
            dist_y = py + math.sin(angle - math.pi * 0.3) * size * 1.5
            screen.blit(dist_text, (dist_x - 15, dist_y + 2))
            
class WaypointManager:
    """Управляет маркерами - только один активный маркер"""
    
    def __init__(self):
        self.waypoint = None  # Только один маркер
    
    def add_waypoint(self, x, y, label=None):
        """Добавляет новый маркер (заменяет старый)"""
        if label is None:
            label = "Marker"
        self.waypoint = Waypoint(x, y, label)
        print(f"[WAYPOINT] Установлен маркер '{label}' в ({int(x)}, {int(y)})")
        return self.waypoint
    
    def remove_waypoint(self):
        """Удаляет текущий маркер"""
        if self.waypoint:
            print(f"[WAYPOINT] Удалён маркер '{self.waypoint.label}'")
            self.waypoint = None
            return True
        return False
    
    def clear_all(self):
        """Удаляет маркер"""
        self.waypoint = None
        print(f"[WAYPOINT] Маркер удалён")
    
    def get_waypoints(self):
        """Возвращает список с одним маркером или пустой список"""
        return [self.waypoint] if self.waypoint else []
    
    def draw_in_game(self, screen, camera, player_x, player_y):
        """Рисует маркер в игре с учётом зума"""
        if not self.waypoint:
            return
        
        wp = self.waypoint
        screen_x, screen_y = camera.world_to_screen(wp.x, wp.y)
        
        if -20 < screen_x < WIDTH + 20 and -20 < screen_y < HEIGHT + 20:
            size = int(12 * camera.zoom)
            pygame.draw.circle(screen, wp.color, (int(screen_x), int(screen_y)), size, 2)
            pygame.draw.line(screen, wp.color, 
                           (screen_x - size * 0.7, screen_y), 
                           (screen_x + size * 0.7, screen_y), 2)
            pygame.draw.line(screen, wp.color, 
                           (screen_x, screen_y - size * 0.7), 
                           (screen_x, screen_y + size * 0.7), 2)
        else:
            # Стрелка на краю
            dx = wp.x - player_x
            dy = wp.y - player_y
            angle = math.atan2(dy, dx)
            
            margin = 60
            cx = WIDTH // 2
            cy = HEIGHT // 2
            
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            t_values = []
            if cos_a > 0:
                t_values.append((WIDTH - margin - cx) / cos_a)
            elif cos_a < 0:
                t_values.append((margin - cx) / cos_a)
            if sin_a > 0:
                t_values.append((HEIGHT - margin - cy) / sin_a)
            elif sin_a < 0:
                t_values.append((margin - cy) / sin_a)
            
            t = min([t for t in t_values if t > 0])
            px = cx + t * cos_a
            py = cy + t * sin_a
            
            size = 15
            tip_x = px + math.cos(angle) * size
            tip_y = py + math.sin(angle) * size
            left_angle = angle + math.pi * 0.7
            right_angle = angle - math.pi * 0.7
            left_x = px + math.cos(left_angle) * size * 0.6
            left_y = py + math.sin(left_angle) * size * 0.6
            right_x = px + math.cos(right_angle) * size * 0.6
            right_y = py + math.sin(right_angle) * size * 0.6
            
            points = [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)]
            pygame.draw.polygon(screen, wp.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 1)    
            
    def draw_on_map(self, screen, world_to_screen, is_visible):
        """Рисует маркер на карте"""
        if self.waypoint:
            self.waypoint.draw_on_map(screen, world_to_screen, is_visible)
            