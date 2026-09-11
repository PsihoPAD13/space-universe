# entities/outpost.py
import pygame
import math
import random
from settings import *

class Outpost:
    """Дружественный аванпост — центр миссий и торговли"""
    
    def __init__(self, x, y, outpost_type='trade'):
        self.x = x
        self.y = y
        self.radius = 40
        self.outpost_type = outpost_type  # 'trade', 'mission', 'repair'
        self.alive = True
        
        # Цвета для разных типов
        self.colors = {
            'trade': (50, 200, 255),    # Голубой - торговля
            'mission': (255, 200, 50),  # Жёлтый - миссии
            'repair': (50, 255, 100),   # Зелёный - ремонт
        }
        self.color = self.colors.get(outpost_type, (100, 100, 255))
        
        # Торговля
        self.resources = {
            'scrap': random.randint(50, 200),
            'crystal': random.randint(10, 50),
            'fuel': random.randint(30, 100),
        }
        
        # Миссии
        self.missions = []
        self._generate_missions()
        
        # Визуальные эффекты
        self.pulse = 0
        self.rotation = 0
    
    def _generate_missions(self):
        """Генерирует доступные миссии"""
        mission_templates = [
            {
                'type': 'kill',
                'name': 'Очистка сектора',
                'description': 'Уничтожьте 10 врагов в секторе',
                'target': 10,
                'reward': {'scrap': 30, 'crystal': 5},
                'progress': 0,
                'active': True
            },
            {
                'type': 'collect',
                'name': 'Сбор ресурсов',
                'description': 'Соберите 50 единиц скрапа',
                'target': 50,
                'reward': {'scrap': 10, 'crystal': 10},
                'progress': 0,
                'active': True
            },
            {
                'type': 'destroy_base',
                'name': 'Уничтожение базы',
                'description': 'Уничтожьте вражескую базу в секторе',
                'target': 1,
                'reward': {'scrap': 50, 'crystal': 20},
                'progress': 0,
                'active': True
            },
            {
                'type': 'explore',
                'name': 'Исследование',
                'description': 'Посетите 3 новых чанка',
                'target': 3,
                'reward': {'scrap': 20, 'crystal': 15},
                'progress': 0,
                'active': True
            },
        ]
        
        # Выбираем 2-3 случайные миссии
        count = random.randint(2, 3)
        self.missions = random.sample(mission_templates, min(count, len(mission_templates)))
    
    def update(self, player):
        """Обновление аванпоста"""
        self.pulse += 0.02
        self.rotation += 0.01
        
        # Проверяем прогресс миссий
        for mission in self.missions:
            if mission['active']:
                if mission['type'] == 'kill':
                    # Прогресс обновляется извне
                    pass
                elif mission['type'] == 'collect':
                    # Прогресс обновляется извне
                    pass
    
    def draw(self, screen, camera):
        """Рисует аванпост с учётом зума"""
        if not self.alive:
            return
        
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        radius = int(self.radius * camera.zoom)
        
        if screen_x < -radius or screen_x > WIDTH + radius or \
           screen_y < -radius or screen_y > HEIGHT + radius:
            return
        
        pulse_scale = 1 + 0.05 * math.sin(self.pulse)
        radius = int(radius * pulse_scale)
        
        # Свечение
        glow = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        glow_color = (self.color[0], self.color[1], self.color[2], 40)
        pygame.draw.circle(glow, glow_color, (radius * 1.5, radius * 1.5), radius * 1.5)
        screen.blit(glow, (int(screen_x - radius * 1.5), int(screen_y - radius * 1.5)))
        
        # Внешнее кольцо
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), radius, 3)
        
        # Внутреннее кольцо
        rot_radius = int(radius * 0.7)
        for i in range(4):
            angle = self.rotation + math.pi / 2 * i
            dx = math.cos(angle) * rot_radius
            dy = math.sin(angle) * rot_radius
            pygame.draw.circle(screen, (150, 150, 200),
                             (int(screen_x + dx), int(screen_y + dy)), max(2, int(4 * camera.zoom)))
        
        # Центр
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), int(radius * 0.2), 2)
        
        # Иконка
        icon_font = pygame.font.Font(None, int(24 * camera.zoom))
        icons = {'trade': '$', 'mission': '!', 'repair': '+'}
        icon = icons.get(self.outpost_type, '?')
        text = icon_font.render(icon, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(int(screen_x), int(screen_y))))

    def interact(self, player, game):
        """Взаимодействие с аванпостом"""
        if self.outpost_type == 'trade':
            return self._show_trade_menu(player, game)
        elif self.outpost_type == 'mission':
            return self._show_mission_menu(player, game)
        elif self.outpost_type == 'repair':
            return self._repair_ship(player, game)
    
    def _show_trade_menu(self, player, game):
        """Показать меню торговли"""
        print(f"\n💰 ТОРГОВЛЯ на аванпосте")
        print(f"   Ваши ресурсы:")
        print(f"   🔩 Скрап: {game.resources['scrap']}")
        print(f"   💎 Кристаллы: {game.resources['crystal']}")
        print(f"   ⛽ Топливо: {game.resources['fuel']}")
        print(f"\n   Ресурсы аванпоста:")
        print(f"   🔩 Скрап: {self.resources['scrap']}")
        print(f"   💎 Кристаллы: {self.resources['crystal']}")
        print(f"   ⛽ Топливо: {self.resources['fuel']}")
        print("\n   Нажмите 1-6 для обмена:")
        print("   1. Скрап -> Кристаллы (10:1)")
        print("   2. Скрап -> Топливо (8:1)")
        print("   3. Кристаллы -> Скрап (1:5)")
        print("   4. Кристаллы -> Топливо (1:3)")
        print("   5. Топливо -> Скрап (1:4)")
        print("   6. Топливо -> Кристаллы (3:1)")
        return 'trade'
    
    def trade(self, game, trade_type):
        """Выполняет обмен ресурсами"""
        if trade_type == 1:  # Скрап -> Кристаллы (10:1)
            if game.resources['scrap'] >= 10:
                game.resources['scrap'] -= 10
                game.resources['crystal'] += 1
                self.resources['scrap'] += 10
                self.resources['crystal'] -= 1
                print("✅ Обмен выполнен: -10 Скрап, +1 Кристалл")
                return True
        elif trade_type == 2:  # Скрап -> Топливо (8:1)
            if game.resources['scrap'] >= 8:
                game.resources['scrap'] -= 8
                game.resources['fuel'] += 1
                self.resources['scrap'] += 8
                self.resources['fuel'] -= 1
                print("✅ Обмен выполнен: -8 Скрап, +1 Топливо")
                return True
        elif trade_type == 3:  # Кристаллы -> Скрап (1:5)
            if game.resources['crystal'] >= 1:
                game.resources['crystal'] -= 1
                game.resources['scrap'] += 5
                self.resources['crystal'] += 1
                self.resources['scrap'] -= 5
                print("✅ Обмен выполнен: -1 Кристалл, +5 Скрап")
                return True
        elif trade_type == 4:  # Кристаллы -> Топливо (1:3)
            if game.resources['crystal'] >= 1:
                game.resources['crystal'] -= 1
                game.resources['fuel'] += 3
                self.resources['crystal'] += 1
                self.resources['fuel'] -= 3
                print("✅ Обмен выполнен: -1 Кристалл, +3 Топливо")
                return True
        elif trade_type == 5:  # Топливо -> Скрап (1:4)
            if game.resources['fuel'] >= 1:
                game.resources['fuel'] -= 1
                game.resources['scrap'] += 4
                self.resources['fuel'] += 1
                self.resources['scrap'] -= 4
                print("✅ Обмен выполнен: -1 Топливо, +4 Скрап")
                return True
        elif trade_type == 6:  # Топливо -> Кристаллы (3:1)
            if game.resources['fuel'] >= 3:
                game.resources['fuel'] -= 3
                game.resources['crystal'] += 1
                self.resources['fuel'] += 3
                self.resources['crystal'] -= 1
                print("✅ Обмен выполнен: -3 Топливо, +1 Кристалл")
                return True
        
        print("❌ Недостаточно ресурсов!")
        return False

    def _show_mission_menu(self, player, game):
        """Показать меню миссий"""
        print(f"\n📋 МИССИИ на аванпосте")
        for i, mission in enumerate(self.missions):
            status = "✅" if mission['progress'] >= mission['target'] else "⏳"
            print(f"   {i+1}. {status} {mission['name']}")
            print(f"      {mission['description']}")
            print(f"      Прогресс: {mission['progress']}/{mission['target']}")
            print(f"      Награда: {mission['reward']}")
        return 'mission'
    
    def _repair_ship(self, player, game):
        """Ремонт корабля"""
        cost = 20  # Скрапа за ремонт
        if game.player_base.resources['scrap'] >= cost:
            game.player_base.resources['scrap'] -= cost
            player.health = player.max_health
            print(f"🔧 Корабль отремонтирован! HP: {player.health}")
            return 'repair'
        else:
            print(f"⚠️ Недостаточно ресурсов! Нужно {cost} скрапа")
            return 'error'