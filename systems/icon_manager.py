# systems/icon_manager.py
import pygame
import os

class IconManager:
    def __init__(self, base_path='assets/sprites/ui/'):
        self.base_path = base_path
        self.icons = {}
        self.load_all_icons()
    
    def load_all_icons(self):
        categories = ['resources', 'stats', 'classes', 'outposts', 
                      'arrows', 'keys', 'map', 'icons']
        
        loaded = 0
        for category in categories:
            path = os.path.join(self.base_path, category)
            if not os.path.exists(path):
                continue
            
            for file in os.listdir(path):
                if file.endswith('.png'):
                    name = file[:-4]
                    try:
                        icon = pygame.image.load(os.path.join(path, file)).convert_alpha()
                        self.icons[name] = icon
                        loaded += 1
                    except Exception as e:
                        print(f"[ICON] ❌ {name}: {e}")
        
        print(f"[ICON] ✅ Загружено {loaded} значков")
    
    def get(self, name):
        return self.icons.get(name)
    
    def draw(self, screen, name, x, y, scale=1.0):
        icon = self.get(name)
        if icon:
            if scale != 1.0:
                w = int(icon.get_width() * scale)
                h = int(icon.get_height() * scale)
                icon = pygame.transform.scale(icon, (w, h))
            screen.blit(icon, (x, y))
            return True
        return False
    
    def draw_with_text(self, screen, name, x, y, text, color=(255, 255, 255), font=None):
        icon = self.get(name)
        offset_x = 0
        
        if icon:
            screen.blit(icon, (x, y))
            offset_x = icon.get_width() + 8
        
        if font:
            text_surf = font.render(text, True, color)
            text_y = y + (icon.get_height() - text_surf.get_height()) // 2 if icon else y
            screen.blit(text_surf, (x + offset_x, text_y))