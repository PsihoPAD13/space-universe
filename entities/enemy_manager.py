# entities/enemy_manager.py
import random
from entities.enemy import Enemy
from entities.enemy_types import ENEMY_TYPES, SPAWN_WEIGHTS

class EnemyManager:
    """Менеджер спавна врагов — централизованное управление"""
    
    def __init__(self):
        self.enemy_types = ENEMY_TYPES
        self.spawn_weights = SPAWN_WEIGHTS
        
        print(f"[ENEMY_MANAGER] Загружено типов врагов: {len(self.enemy_types)}")
        for name, data in self.enemy_types.items():
            print(f"  - {name}: {data['description']}")
    
    def get_available_types(self, current_enemies=None):
        """
        Возвращает список доступных типов с учётом лимитов на экране
        
        Args:
            current_enemies: список текущих врагов (для подсчёта)
        """
        if current_enemies is None:
            return list(self.enemy_types.keys())
        
        # Считаем, сколько врагов каждого типа на экране
        counts = {}
        for enemy in current_enemies:
            counts[enemy.enemy_type] = counts.get(enemy.enemy_type, 0) + 1
        
        # Фильтруем типы, которые не превысили лимит
        available = []
        for name, data in self.enemy_types.items():
            limit = data.get('max_on_screen', 10)  # По умолчанию 10
            current_count = counts.get(name, 0)
            if current_count < limit:
                available.append(name)
        
        return available
    
    def get_spawn_weights(self, types=None):
        """Возвращает веса для спавна"""
        if types is None:
            types = list(self.enemy_types.keys())
        
        weights = []
        for t in types:
            if t in self.spawn_weights:
                weights.append(self.spawn_weights[t])
            else:
                weights.append(10)
        
        return weights
    
    def spawn_enemy(self, x, y, enemy_type=None, sprite_manager=None, 
                    difficulty_multiplier=1.0, base_color=None):
        if enemy_type is None:
            enemy_type = self.get_random_type()
        
        if enemy_type not in self.enemy_types:
            print(f"[ENEMY_MANAGER] Ошибка: тип '{enemy_type}' не найден")
            return None
        
        enemy = Enemy(x, y, enemy_type, sprite_manager, 
                      difficulty_multiplier, base_color)
        return enemy    
    
    def get_random_type(self, current_enemies=None):
        """Возвращает случайный тип врага с учётом весов и лимитов"""
        available = self.get_available_types(current_enemies)
        
        if not available:
            # Если все типы достигли лимита — возвращаем scout
            return 'scout'
        
        weights = self.get_spawn_weights(available)
        
        # Фильтруем типы с нулевым весом
        filtered = [(t, w) for t, w in zip(available, weights) if w > 0]
        if not filtered:
            return 'scout'
        
        types, weights = zip(*filtered)
        return random.choices(types, weights=weights, k=1)[0]
    
    def get_enemy_data(self, enemy_type):
        """Возвращает данные о типе врага"""
        return self.enemy_types.get(enemy_type)
    
    def register_enemy_type(self, name, data):
        """Регистрирует новый тип врага"""
        if name in self.enemy_types:
            print(f"[ENEMY_MANAGER] Тип '{name}' уже существует, перезаписываем")
        
        self.enemy_types[name] = data
        print(f"[ENEMY_MANAGER] Зарегистрирован новый тип: {name}")