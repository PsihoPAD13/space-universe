# world/starfield_background.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT, STAR_LAYERS, STAR_SPAWN_RADIUS_MULTIPLIER


class StarLayer:
    def __init__(self, count, speed, min_size, max_size, min_bright, max_bright, color_chance):
        self.count = count
        self.speed = speed
        self.min_size = min_size
        self.max_size = max_size
        self.min_bright = min_bright
        self.max_bright = max_bright
        self.color_chance = color_chance
        
        self.stars = []
        self.spawn_radius = max(WIDTH, HEIGHT) * STAR_SPAWN_RADIUS_MULTIPLIER
        self.generate_stars(0, 0)
    
    def generate_stars(self, center_x, center_y):
        self.stars = []
        for _ in range(self.count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.spawn_radius)
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            size = random.randint(self.min_size, self.max_size)
            brightness = random.randint(self.min_bright, self.max_bright)
            
            if random.random() < self.color_chance:
                color_variation_type = random.choice([
                    (brightness, brightness, min(255, brightness + 50)),
                    (min(255, brightness + 50), brightness, brightness),
                    (brightness, min(255, brightness + 50), brightness),
                ])
            else:
                color_variation_type = (brightness, brightness, brightness)
            
            self.stars.append({
                'x': x,
                'y': y,
                'size': size,
                'brightness': brightness,
                'color': color_variation_type,
                'phase': random.uniform(0, 6.28),
                '_prev_x': x,
                '_prev_y': y
            })
    
    def update(self, player_x, player_y, offset_x, offset_y):
        for star in self.stars:
            star['_prev_x'] = star['x']
            star['_prev_y'] = star['y']
            
            star['x'] += offset_x * self.speed
            star['y'] += offset_y * self.speed
            
            dx = star['x'] - player_x
            dy = star['y'] - player_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > self.spawn_radius:
                angle = math.atan2(dy, dx) + math.pi + random.uniform(-0.3, 0.3)
                new_dist = self.spawn_radius * 0.9
                star['x'] = player_x + math.cos(angle) * new_dist
                star['y'] = player_y + math.sin(angle) * new_dist
    
    def draw(self, screen, camera, warp_factor=1.0):
        """Рисует звёзды с учётом зума"""
        current_time = pygame.time.get_ticks() * 0.001
        
        for star in self.stars:
            screen_x, screen_y = camera.world_to_screen(star['x'], star['y'])
            
            if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
                twinkle = 0.7 + 0.3 * math.sin(current_time * 0.5 + star['phase'])
                
                color = (
                    min(255, int(star['color'][0] * twinkle * min(warp_factor, 2.5) / 1.5)),
                    min(255, int(star['color'][1] * twinkle * min(warp_factor, 2.5) / 1.5)),
                    min(255, int(star['color'][2] * twinkle * min(warp_factor, 2.5) / 1.5))
                )
                
                # ===== ШЛЕЙФ ПРИ ВАРПЕ =====
                if warp_factor > 1.2 and star['size'] >= 1:
                    trail_length = int((warp_factor - 1.0) * 8) + 2
                    trail_length = min(trail_length, 20)
                    
                    # Направление шлейфа (в экранных координатах)
                    prev_screen_x, prev_screen_y = camera.world_to_screen(
                        star['_prev_x'], star['_prev_y']
                    )
                    
                    dx = screen_x - prev_screen_x
                    dy = screen_y - prev_screen_y
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist > 0:
                        dx /= dist
                        dy /= dist
                    else:
                        dx, dy = 0, 0
                    
                    for i in range(1, trail_length + 1):
                        alpha = int(150 * (1 - i / trail_length) * min(warp_factor / 2, 1.5))
                        alpha = min(255, alpha)
                        
                        trail_x = screen_x - dx * i * 2
                        trail_y = screen_y - dy * i * 2
                        
                        trail_size = max(1, int(star['size'] * (1 - i / trail_length * 0.7) * camera.zoom))
                        
                        trail_color = (
                            min(255, int(color[0] * 0.5)),
                            min(255, int(color[1] * 0.7)),
                            min(255, int(color[2] * 1.2))
                        )
                        
                        surf = pygame.Surface((trail_size * 2 + 2, trail_size * 2 + 2), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (*trail_color, alpha),
                                         (trail_size + 1, trail_size + 1), trail_size)
                        screen.blit(surf, (int(trail_x - trail_size - 1), int(trail_y - trail_size - 1)))
                
                # ===== САМА ЗВЕЗДА =====
                size = max(1, int(star['size'] * min(warp_factor, 1.5) * camera.zoom))
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), size)


class BackgroundStars:
    def __init__(self):
        self.layers = []
        self.warp_factor = 1.0
        self.warp_target = 1.0
        
        for layer_config in STAR_LAYERS:
            count, speed, min_size, max_size, min_bright, max_bright, color_chance = layer_config
            layer = StarLayer(count, speed, min_size, max_size, min_bright, max_bright, color_chance)
            self.layers.append(layer)
    
    def set_warp(self, active):
        if active:
            self.warp_target = 3.0
        else:
            self.warp_target = 1.0
    
    def update(self, player_x, player_y, offset_x, offset_y):
        self.warp_factor += (self.warp_target - self.warp_factor) * 0.05
        
        for layer in self.layers:
            speed_multiplier = 1.0 + (self.warp_factor - 1.0) * 0.3
            layer.update(player_x, player_y, offset_x * speed_multiplier, offset_y * speed_multiplier)
    
    def draw(self, screen, camera):
        """Рисует все слои звёзд с зумом"""
        for layer in self.layers:
            layer.draw(screen, camera, self.warp_factor)