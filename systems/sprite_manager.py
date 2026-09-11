# systems/sprite_manager.py
import pygame
import json
import os

class SpriteManager:
    def __init__(self, config_path='assets/config/sprites.json'):
        self.config_path = config_path
        self.sprites = {}
        self.config = {}
        self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Загружаем ВСЕ категории из папок
            for category in ['ships', 'enemies', 'weapons', 'engines', 'shields']:
                for item_id, data in self.config.get(category, {}).items():
                    if 'folder' in data:
                        self.load_ship_frames(item_id, data['folder'])
            
            print(f"[SPRITE] ✅ Загружено {len(self.sprites)} спрайтов")
            
        except Exception as e:
            print(f"[SPRITE] ❌ Ошибка: {e}")
 
    def load_ship_frames(self, item_id, folder):
        """Загружает 16 кадров из папки"""
        frames = []
        folder_path = f"assets/sprites/{folder}"
        
        if not os.path.exists(folder_path):
            print(f"[SPRITE] ❌ Папка: {folder_path}")
            return
        
        for i in range(16):
            possible = [
                f"{item_id}_bank_{i:02d}.png",
                f"{item_id}_bank_{i}.png",
            ]
            
            found = False
            for name in possible:
                path = os.path.join(folder_path, name)
                if os.path.exists(path):
                    try:
                        frames.append(pygame.image.load(path).convert_alpha())
                        found = True
                        break
                    except:
                        pass
            
            if not found:
                # Заглушка
                frames.append(self._create_fallback_sprite(f"{item_id}_bank_{i}", 32, 32))
        
        if frames:
            self.sprites[f"{item_id}_bank_frames"] = frames
            print(f"[SPRITE] ✅ {item_id}: {len(frames)} кадров")    
    
    def _create_fallback_sprite(self, sprite_id, width, height):
        """Создаёт заглушку"""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 128))
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, width, height), 2)
        return surf
    
    def load_sprite(self, sprite_id, path):
        try:
            sprite = pygame.image.load(path).convert_alpha()
            self.sprites[sprite_id] = sprite
        except Exception as e:
            print(f"[SPRITE] ❌ {sprite_id}: {e}")
    
    def get(self, sprite_id):
        return self.sprites.get(sprite_id)
    
    def get_config(self, category, sprite_id):
        return self.config.get(category, {}).get(sprite_id)
    
    def get_sprite_data(self, category, sprite_id):
        return self.config.get(category, {}).get(sprite_id)
    
    def get_all_in_category(self, category):
        return list(self.config.get(category, {}).keys())
    
    def get_colors(self):
        return self.config.get('colors', {})
    
    def get_slots(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        if not data:
            return []
        slots = data.get('slots', [])
        if isinstance(slots, list):
            return slots
        return []
    
    def get_pivot(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        return data.get('pivot', [0, 0]) if data else [0, 0]
    
    def get_size(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        return data.get('size', [32, 32]) if data else [32, 32]
    
    def get_valid_ships(self):
        """Возвращает корабли с folder"""
        return [sid for sid, d in self.config.get('ships', {}).items() if 'folder' in d]
        
    def get_colored_frames(self, enemy_id, color):
        """Возвращает перекрашенные кадры крена"""
        frames = self.sprites.get(f"{enemy_id}_bank_frames")
        if not frames:
            return None
        
        colored_frames = []
        for frame in frames:
            colored = frame.copy()
            colored.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            colored_frames.append(colored)
        
        return colored_frames