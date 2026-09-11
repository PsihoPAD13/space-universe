# sprite_editor.py
import pygame
import json
import os

pygame.init()

WIDTH, HEIGHT = 1280, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sprite Editor - Space Universe")
clock = pygame.time.Clock()

# Шрифты
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 16)
title_font = pygame.font.Font(None, 32)
tab_font = pygame.font.Font(None, 22)

# Цвета
BG = (25, 25, 40)
PANEL = (40, 40, 60)
BORDER = (80, 80, 120)
GRID = (50, 50, 70)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
DARK_GRAY = (80, 80, 80)
RED = (255, 80, 80)
GREEN = (80, 255, 120)
BLUE = (80, 150, 255)
YELLOW = (255, 220, 80)
ORANGE = (255, 150, 50)
PURPLE = (200, 100, 255)
GOLD = (255, 215, 0)

# Пути
ASSETS = "assets/sprites"
CONFIG = "assets/config/sprites.json"

# Категории
CATEGORIES = {
    'ships': ['ships'],
    'enemies': ['enemies'],
    'weapons': ['weapons'],
    'engines': ['engines'],
    'shields': ['shields']
}

# Типы слотов
SLOT_TYPES = {
    'weapon': {'color': RED, 'label': 'W'},
    'engine': {'color': ORANGE, 'label': 'E'},
    'shield': {'color': BLUE, 'label': 'S'}
}


class SpriteEditor:
    def __init__(self):
        self.running = True
        self.config = {}
        self.load_config()
        
        # Текущий спрайт
        self.sprite = None
        self.sprite_name = ""
        self.sprite_path = ""
        self.sprite_folder = ""
        self.category = "ships"
        
        # Параметры
        self.pivot_x = 64
        self.pivot_y = 64
        self.offset_x = 0
        self.offset_y = 0
        self.size = 128
        self.angle = 0
        self.scale = 2.0
        
        # Режимы
        self.mode = "slots"
        self.dragging = False
        self.dragging_slot = None
        
        # Слоты
        self.slots = []
        
        # ===== ПАРАМЕТРЫ =====
        # Корабли
        self.hp_value = 100
        self.speed_value = 1.0
        
        # Оружие
        self.weapon_type = "static"
        self.damage_value = 10
        self.fire_rate_value = 0.3
        
        # Двигатели
        self.thrust_value = 1.0
        self.fuel_value = 0.8
        
        # Щиты
        self.shield_power = 50
        self.shield_regen = 1
        
        # Враги
        self.enemy_hp = 2
        self.enemy_speed = 3.0
        self.enemy_behavior = "chase"
        self.enemy_score = 10
        self.enemy_can_shoot = True
        self.enemy_shoot_delay = 60
        self.enemy_bullet_speed = 5
        self.enemy_bullet_type = "forward"
        
        # Стоимость
        self.price_value = 100
        
        # Кнопки параметров
        self.param_buttons = {}
        
        # Выпадающие списки
        self.dropdown_open = None
        self.dropdown_items = {}
        self.dropdown_rects = {}
        self.dropdown_positions = {}
        
        # Список
        self.sprite_list = []
        self.selected_index = 0
        self.scroll = 0
        
        # Вкладки
        self.tabs = ['ships', 'enemies', 'weapons', 'engines', 'shields']
        self.current_tab = 0
        
        # Иконки
        self.icons = {}
        self.load_icons()
        
        self.load_sprite_list()
    
    def load_config(self):
        try:
            with open(CONFIG, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"[EDITOR] Конфиг загружен")
        except:
            self.config = {}
    
    def save_config(self):
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[EDITOR] Конфиг сохранён")
            return True
        except Exception as e:
            print(f"[EDITOR] Ошибка: {e}")
            return False
    
    def load_icons(self):
        ui_path = os.path.join(ASSETS, 'ui')
        
        keys = ['key_e', 'key_enter', 'key_h', 'key_r']
        for key in keys:
            path = os.path.join(ui_path, 'keys', f"{key}.png")
            if os.path.exists(path):
                self.icons[key] = pygame.image.load(path).convert_alpha()
        
        arrows = ['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right']
        for arrow in arrows:
            path = os.path.join(ui_path, 'arrows', f"{arrow}.png")
            if os.path.exists(path):
                self.icons[arrow] = pygame.image.load(path).convert_alpha()
    
    def load_sprite_list(self):
        self.sprite_list = []
        tab = self.tabs[self.current_tab]
        
        # ===== ВСЕ КАТЕГОРИИ ТЕПЕРЬ ИЗ ПАПОК =====
        folder_path = os.path.join(ASSETS, tab)
        if os.path.exists(folder_path):
            for folder in sorted(os.listdir(folder_path)):
                subfolder = os.path.join(folder_path, folder)
                if os.path.isdir(subfolder):
                    png_files = [f for f in sorted(os.listdir(subfolder)) if f.endswith('.png')]
                    if png_files:
                        self.sprite_list.append({
                            'name': folder,
                            'path': f"{tab}/{folder}/{png_files[0]}",
                            'category': tab,
                            'folder': folder
                        })
        
        if self.sprite_list:
            self.load_sprite(0)
        else:
            self.sprite = None
            self.sprite_name = ""
    
    def load_sprite(self, index):
        if not (0 <= index < len(self.sprite_list)):
            return
        self.selected_index = index
        data = self.sprite_list[index]
        self.sprite_name = data['name']
        self.sprite_path = data['path']
        self.category = data['category']
        self.sprite_folder = data.get('folder', '')
        
        full_path = os.path.join(ASSETS, self.sprite_path)
        try:
            self.sprite = pygame.image.load(full_path).convert_alpha()
            self.size = self.sprite.get_width()
            
            saved = self.config.get(self.category, {}).get(self.sprite_name, {})
            
            # Общие
            self.pivot_x = saved.get('pivot', [self.size//2, self.size//2])[0]
            self.pivot_y = saved.get('pivot', [self.size//2, self.size//2])[1]
            self.offset_x = saved.get('x', 0)
            self.offset_y = saved.get('y', 0)
            self.angle = 0
            self.slots = saved.get('slots', [])
            self.price_value = saved.get('price', 100)
            
            stats = saved.get('stats', {})
            
            if self.category == 'ships':
                self.hp_value = stats.get('hp', 100)
                self.speed_value = stats.get('speed', 1.0)
            
            elif self.category == 'enemies':
                self.enemy_hp = stats.get('hp', 2)
                self.enemy_speed = stats.get('speed', 3.0)
                self.enemy_behavior = stats.get('behavior', 'chase')
                self.enemy_score = stats.get('score', 10)
                self.enemy_can_shoot = stats.get('can_shoot', True)
                self.enemy_shoot_delay = stats.get('shoot_delay', 60)
                self.enemy_bullet_speed = stats.get('bullet_speed', 5)
                self.enemy_bullet_type = stats.get('bullet_type', 'forward')
            
            elif self.category == 'weapons':
                self.weapon_type = saved.get('type', 'static')
                self.damage_value = stats.get('damage', 10)
                self.fire_rate_value = stats.get('fire_rate', 0.3)
            
            elif self.category == 'engines':
                self.thrust_value = stats.get('thrust', 1.0)
                self.fuel_value = stats.get('fuel_consumption', 0.8)
            
            elif self.category == 'shields':
                self.shield_power = stats.get('power', 50)
                self.shield_regen = stats.get('regen', 1)
            
            print(f"[EDITOR] Загружен: {self.sprite_name} ({self.size}px)")
        except Exception as e:
            print(f"[EDITOR] Ошибка: {e}")
            self.sprite = None
    
    def save_current(self):
        if not self.sprite_name:
            return
        
        if self.category not in self.config:
            self.config[self.category] = {}
        
        data = {
            "folder": f"{self.category}/{self.sprite_name}/",  # <-- ВСЕГДА ПАПКА
            "size": [self.size, self.size],
            "pivot": [int(self.pivot_x), int(self.pivot_y)],
            "x": int(self.offset_x),
            "y": int(self.offset_y),
            "slots": self.slots if self.slots else [],
            "price": int(self.price_value)
        }
        
        # ===== СТАТЫ ПО КАТЕГОРИИ =====
        if self.category == 'ships':
            data["stats"] = {
                "hp": int(self.hp_value),
                "speed": round(self.speed_value, 2)
            }
        
        elif self.category == 'enemies':
            data["stats"] = {
                "hp": int(self.enemy_hp),
                "speed": round(self.enemy_speed, 1),
                "behavior": self.enemy_behavior,
                "score": int(self.enemy_score),
                "can_shoot": self.enemy_can_shoot,
                "shoot_delay": int(self.enemy_shoot_delay),
                "bullet_speed": int(self.enemy_bullet_speed),
                "bullet_type": self.enemy_bullet_type
            }
        
        elif self.category == 'weapons':
            data["type"] = self.weapon_type
            data["stats"] = {
                "damage": int(self.damage_value),
                "fire_rate": round(self.fire_rate_value, 2)
            }
        
        elif self.category == 'engines':
            data["stats"] = {
                "thrust": round(self.thrust_value, 2),
                "fuel_consumption": round(self.fuel_value, 2)
            }
        
        elif self.category == 'shields':
            data["stats"] = {
                "power": int(self.shield_power),
                "regen": int(self.shield_regen)
            }
        
        self.config[self.category][self.sprite_name] = data
        self.save_config()
        print(f"[EDITOR] Сохранён: {self.sprite_name} ({self.category})")
    
    def add_slot(self, slot_type):
        if self.category not in ['ships', 'enemies']:
            print("[EDITOR] Слоты только для кораблей и врагов!")
            return
        
        new_slot = {
            'type': slot_type,
            'x': 0,
            'y': 0,
            'z': 0.5
        }
        self.slots.append(new_slot)
        print(f"[EDITOR] Добавлен слот: {slot_type}")
    
    def remove_last_slot(self):
        if self.slots:
            removed = self.slots.pop()
            print(f"[EDITOR] Удалён слот: {removed.get('type', '?')}")
    
    def switch_tab(self, direction):
        self.current_tab = (self.current_tab + direction) % len(self.tabs)
        self.scroll = 0
        self.load_sprite_list()
        print(f"[EDITOR] Вкладка: {self.tabs[self.current_tab]}")
    
    def _change_param(self, param_id, direction):
        if param_id == 'hp':
            self.hp_value = max(10, min(1000, self.hp_value + direction * 10))
        elif param_id == 'speed':
            self.speed_value = max(0.1, min(5.0, round(self.speed_value + direction * 0.1, 1)))
        elif param_id == 'damage':
            self.damage_value = max(1, min(100, self.damage_value + direction))
        elif param_id == 'fire_rate':
            self.fire_rate_value = max(0.05, min(2.0, round(self.fire_rate_value + direction * 0.05, 2)))
        elif param_id == 'thrust':
            self.thrust_value = max(0.1, min(5.0, round(self.thrust_value + direction * 0.1, 1)))
        elif param_id == 'fuel':
            self.fuel_value = max(0.1, min(5.0, round(self.fuel_value + direction * 0.1, 1)))
        elif param_id == 'power':
            self.shield_power = max(10, min(500, self.shield_power + direction * 10))
        elif param_id == 'regen':
            self.shield_regen = max(0, min(10, self.shield_regen + direction))
        elif param_id == 'price':
            self.price_value = max(0, min(10000, self.price_value + direction * 10))
        elif param_id == 'enemy_hp':
            self.enemy_hp = max(1, min(50, self.enemy_hp + direction))
        elif param_id == 'enemy_speed':
            self.enemy_speed = max(0.1, min(10.0, round(self.enemy_speed + direction * 0.1, 1)))
        elif param_id == 'enemy_score':
            self.enemy_score = max(1, min(500, self.enemy_score + direction * 5))
        elif param_id == 'enemy_shoot_delay':
            self.enemy_shoot_delay = max(10, min(300, self.enemy_shoot_delay + direction * 5))
        elif param_id == 'enemy_bullet_speed':
            self.enemy_bullet_speed = max(1, min(20, self.enemy_bullet_speed + direction))
    
    def _apply_dropdown_choice(self, param_id, value):
        if param_id == 'weapon_type':
            self.weapon_type = value
        elif param_id == 'enemy_behavior':
            self.enemy_behavior = value
        elif param_id == 'enemy_can_shoot':
            self.enemy_can_shoot = (value == 'yes')
        elif param_id == 'enemy_bullet_type':
            self.enemy_bullet_type = value
        
        print(f"[EDITOR] {param_id} = {value}")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_current()
                elif event.key == pygame.K_r:
                    self.angle = 0
                elif event.key == pygame.K_1:
                    self.mode = "view"
                elif event.key == pygame.K_2:
                    self.mode = "pivot"
                elif event.key == pygame.K_3:
                    self.mode = "offset"
                elif event.key == pygame.K_4:
                    self.mode = "slots"
                elif event.key == pygame.K_a and self.mode == "slots":
                    self.add_slot('weapon')
                elif event.key == pygame.K_d and self.mode == "slots":
                    self.add_slot('engine')
                elif event.key == pygame.K_s and self.mode == "slots" and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.add_slot('shield')
                elif event.key == pygame.K_DELETE and self.mode == "slots":
                    self.remove_last_slot()
                elif event.key == pygame.K_TAB:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.switch_tab(-1)
                    else:
                        self.switch_tab(1)
                elif event.key == pygame.K_UP:
                    self.scroll = max(0, self.scroll - 1)
                elif event.key == pygame.K_DOWN:
                    self.scroll = min(max(0, len(self.sprite_list) - 15), self.scroll + 1)
                elif event.key == pygame.K_LEFT:
                    self.load_sprite(max(0, self.selected_index - 1))
                elif event.key == pygame.K_RIGHT:
                    self.load_sprite(min(len(self.sprite_list) - 1, self.selected_index + 1))
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.scale = min(4.0, self.scale + 0.2)
                elif event.key == pygame.K_MINUS:
                    self.scale = max(0.5, self.scale - 0.2)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                if event.button == 1:
                    # ===== ВЫПАДАЮЩИЕ СПИСКИ =====
                    if self.dropdown_open:
                        param_id = self.dropdown_open
                        if param_id in self.dropdown_positions:
                            x, y = self.dropdown_positions[param_id]
                            items = self.dropdown_items.get(param_id, [])
                            
                            for i, item in enumerate(items):
                                item_rect = pygame.Rect(x, y + i * 28, 150, 28)
                                if item_rect.collidepoint(mx, my):
                                    self._apply_dropdown_choice(param_id, item)
                                    self.dropdown_open = None
                                    return
                            
                            self.dropdown_open = None
                            return
                    
                    # Проверяем клик по кнопкам выпадающих списков
                    for param_id, rect in self.dropdown_rects.items():
                        if rect.collidepoint(mx, my):
                            self.dropdown_open = param_id
                            return
                    
                    # Клик по вкладкам
                    for i, tab in enumerate(self.tabs):
                        tab_rect = pygame.Rect(230 + i * 110, 50, 105, 30)
                        if tab_rect.collidepoint(mx, my):
                            self.current_tab = i
                            self.scroll = 0
                            self.load_sprite_list()
                            return
                    
                    # Клик по списку
                    for i in range(15):
                        idx = self.scroll + i
                        if idx < len(self.sprite_list):
                            rect = pygame.Rect(10, 100 + i * 28, 200, 25)
                            if rect.collidepoint(mx, my):
                                self.load_sprite(idx)
                                return
                    
                    # Клик по кнопкам параметров
                    for param_id, buttons in self.param_buttons.items():
                        if buttons['minus'].collidepoint(mx, my):
                            self._change_param(param_id, -1)
                            return
                        if buttons['plus'].collidepoint(mx, my):
                            self._change_param(param_id, 1)
                            return
                    
                    # Клик по спрайту
                    if self.sprite:
                        sprite_x = 250
                        sprite_y = 100
                        
                        if self.mode == "slots" and self.category in ['ships', 'enemies']:
                            for i, slot in enumerate(self.slots):
                                sx = sprite_x + (self.size/2 + slot['x']) * self.scale
                                sy = sprite_y + (self.size/2 + slot['y']) * self.scale
                                if abs(mx - sx) < 15 and abs(my - sy) < 15:
                                    self.dragging_slot = i
                                    return
                        
                        sprite_rect = pygame.Rect(sprite_x, sprite_y, self.size * self.scale, self.size * self.scale)
                        if sprite_rect.collidepoint(mx, my):
                            self.dragging = True
                
                elif event.button == 3 and self.mode == "slots":
                    sprite_x = 250
                    sprite_y = 100
                    for i, slot in enumerate(self.slots):
                        sx = sprite_x + (self.size/2 + slot['x']) * self.scale
                        sy = sprite_y + (self.size/2 + slot['y']) * self.scale
                        if abs(mx - sx) < 15 and abs(my - sy) < 15:
                            self.slots.pop(i)
                            return
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
                self.dragging_slot = None
            
            elif event.type == pygame.MOUSEMOTION:
                sprite_x = 250
                sprite_y = 100
                
                if self.dragging and self.sprite:
                    local_x = (event.pos[0] - sprite_x) / self.scale
                    local_y = (event.pos[1] - sprite_y) / self.scale
                    
                    if self.mode == "pivot":
                        self.pivot_x = max(0, min(self.size, local_x))
                        self.pivot_y = max(0, min(self.size, local_y))
                    elif self.mode == "offset":
                        center = self.size / 2
                        self.offset_x = local_x - center
                        self.offset_y = local_y - center
                
                elif self.dragging_slot is not None:
                    local_x = (event.pos[0] - sprite_x) / self.scale
                    local_y = (event.pos[1] - sprite_y) / self.scale
                    
                    self.slots[self.dragging_slot]['x'] = local_x - self.size/2
                    self.slots[self.dragging_slot]['y'] = local_y - self.size/2
    
    def draw_tabs(self):
        for i, tab in enumerate(self.tabs):
            rect = pygame.Rect(230 + i * 110, 50, 105, 30)
            
            if i == self.current_tab:
                pygame.draw.rect(screen, (80, 80, 140), rect)
                pygame.draw.rect(screen, YELLOW, rect, 2)
                color = WHITE
            else:
                pygame.draw.rect(screen, (40, 40, 60), rect)
                pygame.draw.rect(screen, BORDER, rect, 1)
                color = GRAY
            
            text = tab_font.render(tab.upper(), True, color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
    
    def draw_param_row(self, x, y, label, value, param_id):
        text = small_font.render(f"{label}:", True, GRAY)
        screen.blit(text, (x + 15, y))
        
        minus_rect = pygame.Rect(x + 100, y - 5, 25, 25)
        pygame.draw.rect(screen, (80, 40, 40), minus_rect)
        pygame.draw.rect(screen, RED, minus_rect, 1)
        minus_text = font.render("-", True, WHITE)
        screen.blit(minus_text, minus_text.get_rect(center=minus_rect.center))
        
        if isinstance(value, float):
            val_text = font.render(f"{value:.1f}", True, WHITE)
        else:
            val_text = font.render(str(value), True, WHITE)
        val_rect = val_text.get_rect(center=(x + 150, y + 8))
        screen.blit(val_text, val_rect)
        
        plus_rect = pygame.Rect(x + 180, y - 5, 25, 25)
        pygame.draw.rect(screen, (40, 80, 40), plus_rect)
        pygame.draw.rect(screen, GREEN, plus_rect, 1)
        plus_text = font.render("+", True, WHITE)
        screen.blit(plus_text, plus_text.get_rect(center=plus_rect.center))
        
        self.param_buttons[param_id] = {'minus': minus_rect, 'plus': plus_rect}
    
    def draw_dropdown(self, panel_x, y, label, current_value, items, param_id):
        text = small_font.render(f"{label}:", True, GRAY)
        screen.blit(text, (panel_x + 15, y))
        
        value_rect = pygame.Rect(panel_x + 120, y - 5, 150, 28)
        pygame.draw.rect(screen, (60, 60, 90), value_rect)
        pygame.draw.rect(screen, YELLOW, value_rect, 1)
        
        # Стрелка
        arrow_x = value_rect.right - 20
        arrow_y = value_rect.centery
        pygame.draw.polygon(screen, WHITE, [
            (arrow_x - 5, arrow_y - 3),
            (arrow_x + 5, arrow_y - 3),
            (arrow_x, arrow_y + 3)
        ])
        
        value_text = font.render(str(current_value), True, WHITE)
        screen.blit(value_text, (value_rect.x + 10, value_rect.y + 5))
        
        self.dropdown_rects[param_id] = value_rect
        self.dropdown_items[param_id] = items
        self.dropdown_positions[param_id] = (value_rect.x, value_rect.bottom)
        
        # Открытый список
        if self.dropdown_open == param_id:
            list_rect = pygame.Rect(value_rect.x, value_rect.bottom, value_rect.width, len(items) * 28)
            pygame.draw.rect(screen, (40, 40, 70), list_rect)
            pygame.draw.rect(screen, YELLOW, list_rect, 2)
            
            for i, item in enumerate(items):
                item_rect = pygame.Rect(value_rect.x, value_rect.bottom + i * 28, value_rect.width, 28)
                
                mx, my = pygame.mouse.get_pos()
                if item_rect.collidepoint(mx, my):
                    pygame.draw.rect(screen, (80, 80, 140), item_rect)
                
                item_text = font.render(str(item), True, WHITE)
                screen.blit(item_text, (item_rect.x + 10, item_rect.y + 5))
        
        return y + 35
    
    def draw_params_panel(self, panel_x, y):
        title = font.render("STATS", True, YELLOW)
        screen.blit(title, (panel_x + 15, y))
        y += 35
        
        self.param_buttons.clear()
        self.dropdown_rects.clear()
        
        if self.category == 'ships':
            self.draw_param_row(panel_x, y, "HP", self.hp_value, "hp")
            y += 35
            self.draw_param_row(panel_x, y, "Speed", self.speed_value, "speed")
            y += 35
            self.draw_param_row(panel_x, y, "Price", self.price_value, "price")
            y += 35
        
        elif self.category == 'enemies':
            self.draw_param_row(panel_x, y, "HP", self.enemy_hp, "enemy_hp")
            y += 35
            self.draw_param_row(panel_x, y, "Speed", self.enemy_speed, "enemy_speed")
            y += 35
            self.draw_param_row(panel_x, y, "Score", self.enemy_score, "enemy_score")
            y += 35
            
            y = self.draw_dropdown(panel_x, y, "Behavior", self.enemy_behavior,
                                   ['chase', 'stationary', 'kamikaze', 'orbit'], 'enemy_behavior')
            
            y = self.draw_dropdown(panel_x, y, "Can Shoot", 
                                   "yes" if self.enemy_can_shoot else "no",
                                   ['yes', 'no'], 'enemy_can_shoot')
            
            if self.enemy_can_shoot:
                self.draw_param_row(panel_x, y, "Shoot Delay", self.enemy_shoot_delay, "enemy_shoot_delay")
                y += 35
                self.draw_param_row(panel_x, y, "Bullet Speed", self.enemy_bullet_speed, "enemy_bullet_speed")
                y += 35
                
                y = self.draw_dropdown(panel_x, y, "Bullet Type", self.enemy_bullet_type,
                                       ['forward', 'target'], 'enemy_bullet_type')
        
        elif self.category == 'weapons':
            y = self.draw_dropdown(panel_x, y, "Type", self.weapon_type,
                                   ['static', 'turret'], 'weapon_type')
            
            self.draw_param_row(panel_x, y, "Damage", self.damage_value, "damage")
            y += 35
            self.draw_param_row(panel_x, y, "Fire Rate", self.fire_rate_value, "fire_rate")
            y += 35
            self.draw_param_row(panel_x, y, "Price", self.price_value, "price")
            y += 35
        
        elif self.category == 'engines':
            self.draw_param_row(panel_x, y, "Thrust", self.thrust_value, "thrust")
            y += 35
            self.draw_param_row(panel_x, y, "Fuel", self.fuel_value, "fuel")
            y += 35
            self.draw_param_row(panel_x, y, "Price", self.price_value, "price")
            y += 35
        
        elif self.category == 'shields':
            self.draw_param_row(panel_x, y, "Power", self.shield_power, "power")
            y += 35
            self.draw_param_row(panel_x, y, "Regen", self.shield_regen, "regen")
            y += 35
            self.draw_param_row(panel_x, y, "Price", self.price_value, "price")
            y += 35
        
        return y
    
    def draw_hints(self):
        hint_y = HEIGHT - 60
        
        y = hint_y
        text = small_font.render("Switch category:", True, GRAY)
        screen.blit(text, (250, y + 5))
        tab_text = font.render("[TAB]", True, YELLOW)
        screen.blit(tab_text, (400, y))
        
        y += 25
        
        if 'arrow_up' in self.icons:
            icon = pygame.transform.scale(self.icons['arrow_up'], (20, 20))
            screen.blit(icon, (250, y))
        if 'arrow_down' in self.icons:
            icon = pygame.transform.scale(self.icons['arrow_down'], (20, 20))
            screen.blit(icon, (275, y))
        text = small_font.render("Scroll", True, GRAY)
        screen.blit(text, (300, y + 5))
        
        if 'arrow_left' in self.icons:
            icon = pygame.transform.scale(self.icons['arrow_left'], (20, 20))
            screen.blit(icon, (380, y))
        if 'arrow_right' in self.icons:
            icon = pygame.transform.scale(self.icons['arrow_right'], (20, 20))
            screen.blit(icon, (405, y))
        text = small_font.render("Select", True, GRAY)
        screen.blit(text, (430, y + 5))
        
        ctrl_text = font.render("[CTRL+S]", True, GREEN)
        screen.blit(ctrl_text, (510, y))
        text = small_font.render("Save", True, GRAY)
        screen.blit(text, (595, y + 5))
    
    def draw(self):
        screen.fill(BG)
        
        # ===== ЛЕВАЯ ПАНЕЛЬ =====
        pygame.draw.rect(screen, PANEL, (0, 0, 220, HEIGHT))
        pygame.draw.line(screen, BORDER, (220, 0), (220, HEIGHT), 2)
        
        title = title_font.render("SPRITES", True, YELLOW)
        screen.blit(title, (10, 10))
        
        for i in range(15):
            idx = self.scroll + i
            if idx >= len(self.sprite_list):
                break
            
            data = self.sprite_list[idx]
            rect = pygame.Rect(10, 100 + i * 28, 200, 25)
            
            if idx == self.selected_index:
                pygame.draw.rect(screen, (60, 60, 120), rect)
                pygame.draw.rect(screen, YELLOW, rect, 1)
                color = WHITE
            else:
                color = GRAY
            
            name = data['name'][:20]
            text = small_font.render(name, True, color)
            screen.blit(text, (15, 105 + i * 28))
        
        # ===== ВКЛАДКИ =====
        self.draw_tabs()
        
        # ===== ЦЕНТР =====
        if self.sprite:
            sprite_x = 250
            sprite_y = 100
            sprite_size = self.size * self.scale
            
            # Сетка
            for i in range(0, int(sprite_size) + 1, int(16 * self.scale)):
                x = sprite_x + i
                pygame.draw.line(screen, GRID, (x, sprite_y), (x, sprite_y + sprite_size), 1)
            for i in range(0, int(sprite_size) + 1, int(16 * self.scale)):
                y = sprite_y + i
                pygame.draw.line(screen, GRID, (sprite_x, y), (sprite_x + sprite_size, y), 1)
            
            # Спрайт
            scaled = pygame.transform.scale(self.sprite, (int(sprite_size), int(sprite_size)))
            rotated = pygame.transform.rotate(scaled, self.angle)
            rect = rotated.get_rect(center=(sprite_x + sprite_size//2, sprite_y + sprite_size//2))
            screen.blit(rotated, rect)
            
            # Pivot
            px = sprite_x + self.pivot_x * self.scale
            py = sprite_y + self.pivot_y * self.scale
            pygame.draw.circle(screen, RED, (int(px), int(py)), 10, 2)
            pygame.draw.circle(screen, RED, (int(px), int(py)), 4)
            
            # Offset
            ox = px + self.offset_x * self.scale
            oy = py + self.offset_y * self.scale
            pygame.draw.circle(screen, GREEN, (int(ox), int(oy)), 8, 2)
            pygame.draw.line(screen, GREEN, (px, py), (ox, oy), 2)
            
            # Слоты
            if self.category in ['ships', 'enemies']:
                for i, slot in enumerate(self.slots):
                    slot_type = slot.get('type', 'weapon')
                    sx = sprite_x + (self.size/2 + slot['x']) * self.scale
                    sy = sprite_y + (self.size/2 + slot['y']) * self.scale
                    
                    color = SLOT_TYPES.get(slot_type, SLOT_TYPES['weapon'])['color']
                    label = SLOT_TYPES.get(slot_type, SLOT_TYPES['weapon'])['label']
                    
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), 12, 2)
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), 8)
                    
                    slot_font = pygame.font.Font(None, 16)
                    text = slot_font.render(label, True, WHITE)
                    screen.blit(text, text.get_rect(center=(int(sx), int(sy))))
            
            # Информация
            info_y = sprite_y + sprite_size + 20
            info = f"{self.sprite_name}  {self.size}x{self.size}"
            text = font.render(info, True, WHITE)
            screen.blit(text, (250, info_y))
            
            info2 = f"Category: {self.category}"
            text2 = small_font.render(info2, True, ORANGE)
            screen.blit(text2, (250, info_y + 30))
        
        # ===== ПРАВАЯ ПАНЕЛЬ =====
        panel_x = 1000
        pygame.draw.rect(screen, PANEL, (panel_x, 0, WIDTH - panel_x, HEIGHT))
        pygame.draw.line(screen, BORDER, (panel_x, 0), (panel_x, HEIGHT), 2)
        
        title = title_font.render("PARAMS", True, YELLOW)
        screen.blit(title, (panel_x + 15, 10))
        
        y = 60
        
        modes = [("View", "1"), ("Pivot", "2"), ("Offset", "3"), ("Slots", "4")]
        for i, (name, key) in enumerate(modes):
            color = GREEN if self.mode == name.lower() else GRAY
            text = font.render(f"[{key}] {name}", True, color)
            screen.blit(text, (panel_x + 15 + (i % 2) * 120, y + (i // 2) * 25))
        y += 70
        
        if self.sprite:
            y = self.draw_params_panel(panel_x, y)
        
        y += 20
        save_rect = pygame.Rect(panel_x + 15, y, 200, 40)
        pygame.draw.rect(screen, (40, 80, 40), save_rect)
        pygame.draw.rect(screen, GREEN, save_rect, 2)
        text = font.render("CTRL+S Save", True, WHITE)
        screen.blit(text, text.get_rect(center=save_rect.center))
        
        self.draw_hints()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    editor = SpriteEditor()
    editor.run()