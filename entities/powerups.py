# entities/powerups.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT, WHITE, CHUNK_SIZE

class PowerUp:
    """Базовый класс бонуса"""
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.radius = 15
        self.speed = 1.5
        self.angle = 0
        self.collected = False
        self.lifetime = 600
        self.pulse = 0
        self.current_radius = self.radius
        
        self.types = {
            'health': {
                'color': (255, 50, 50),
                'symbol': '+',
                'name': 'Health +25'
            },
            'shield': {
                'color': (50, 150, 255),
                'symbol': 'S',
                'name': 'Shield'
            },
            'triple_shot': {
                'color': (255, 200, 50),
                'symbol': '3',
                'name': 'Triple Shot'
            },
            'speed_boost': {
                'color': (50, 255, 150),
                'symbol': '>',
                'name': 'Speed Boost'
            },
            'bomb': {
                'color': (255, 100, 200),
                'symbol': '!',
                'name': 'Bomb'
            },
            'magnet': {
                'color': (200, 100, 255),
                'symbol': 'M',
                'name': 'Magnet'
            }
        }
    
    def update(self):
        self.angle += 0.02
        self.pulse += 0.05
        self.lifetime -= 1
        self.y += self.speed * 0.3
        self.current_radius = self.radius + 3 * math.sin(self.pulse)
    
    def draw(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        current_radius = self.current_radius * camera.zoom
        
        if screen_x < -50 or screen_x > WIDTH + 50 or \
           screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        type_data = self.types.get(self.type, self.types['health'])
        color = type_data['color']
        
        glow_size = int(current_radius * 1.5)
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (color[0], color[1], color[2], 50), (glow_size, glow_size), glow_size)
        screen.blit(glow, (int(screen_x - glow_size), int(screen_y - glow_size)))
        
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), int(current_radius), 2)
        
        # Символ
        font_size = max(8, int(32 * camera.zoom))
        font = pygame.font.Font(None, font_size)
        text = font.render(type_data['symbol'], True, WHITE)
        screen.blit(text, text.get_rect(center=(int(screen_x), int(screen_y))))

class PowerUpSystem:
    def __init__(self):
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_delay = 300
        self.active_effects = {}
    
    def spawn_powerup(self, x, y):
        types = ['health', 'shield', 'triple_shot', 'speed_boost', 'bomb', 'magnet']
        weights = [30, 20, 15, 15, 10, 10]
        powerup_type = random.choices(types, weights=weights, k=1)[0]
        self.powerups.append(PowerUp(x, y, powerup_type))
    
    def spawn_random(self):
        x = random.randint(-CHUNK_SIZE * 2, CHUNK_SIZE * 2)
        y = random.randint(-CHUNK_SIZE * 2, CHUNK_SIZE * 2)
        self.spawn_powerup(x, y)
    
    def spawn_from_enemy(self, x, y, chance=0.3):
        if random.random() < chance:
            self.spawn_powerup(x, y)
    
    def update(self, player_x, player_y):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_random()
            self.spawn_timer = 0
        
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.lifetime <= 0:
                self.powerups.remove(powerup)
    
    def check_collection(self, ship, particle_system=None):
        collected = []
        
        for powerup in self.powerups[:]:
            dx = ship.x - powerup.x
            dy = ship.y - powerup.y
            dist = math.sqrt(dx**2 + dy**2)
            
            collect_radius = ship.radius + powerup.radius + 10
            
            if 'magnet' in self.active_effects:
                collect_radius *= 2.5
            
            if dist < collect_radius:
                powerup.collected = True
                collected.append(powerup)
                self.powerups.remove(powerup)
                
                if particle_system:
                    particle_system.spawn_explosion(
                        powerup.x, powerup.y,
                        count=15,
                        speed=3,
                        colors=[powerup.types[powerup.type]['color'], (255, 255, 255)]
                    )
                
                self.apply_effect(ship, powerup.type)
        
        return collected
    
    def apply_effect(self, ship, effect_type):
        if effect_type == 'health':
            ship.health = min(ship.max_health, ship.health + 25)
            #print(f"Health restored! HP: {ship.health}")
            
        elif effect_type == 'shield':
            self.active_effects['shield'] = 300
            ship.shield_active = True
            #print("Shield activated!")
            
        elif effect_type == 'triple_shot':
            self.active_effects['triple_shot'] = 600
            #print("Triple Shot activated!")
            
        elif effect_type == 'speed_boost':
            self.active_effects['speed_boost'] = 400
            #print("Speed Boost activated!")
            
        elif effect_type == 'bomb':
            self.active_effects['bomb'] = 1
            #print("Bomb activated!")
            
        elif effect_type == 'magnet':
            self.active_effects['magnet'] = 400
            #print("Magnet activated!")
    
    def update_effects(self, ship):
        for effect in list(self.active_effects.keys()):
            self.active_effects[effect] -= 1
            if self.active_effects[effect] <= 0:
                del self.active_effects[effect]
                if effect == 'shield':
                    ship.shield_active = False
                elif effect == 'speed_boost':
                    ship.max_speed = ship.normal_max_speed  # <-- ИСПРАВЛЕНО
                    print(f"[POWERUP] Speed boost expired, speed = {ship.max_speed}")
        
        if 'speed_boost' in self.active_effects:
            ship.max_speed = 12
        else:
            ship.max_speed = ship.normal_max_speed  # <-- ИСПРАВЛЕНО
        
        if 'shield' in self.active_effects:
            ship.shield_active = True
    
    def draw(self, screen, camera):
        for powerup in self.powerups:
            powerup.draw(screen, camera)
    
    def clear(self):
        self.powerups.clear()
        self.active_effects.clear()