# settings.py
import pygame

# ===== РАЗМЕР ЭКРАНА =====
WIDTH, HEIGHT = 1280, 720
FPS = 60

# ===== БЕСКОНЕЧНЫЙ МИР =====
# Мир не имеет границ!

# ===== РАЗМЕР ЧАНКА =====
CHUNK_SIZE = 16384  # пикселей (8к)

# ===== РАЗМЕР РЕГИОНА =====
REGION_CHUNKS = 16  # 16x16 чанков в регионе
REGION_SIZE = CHUNK_SIZE * REGION_CHUNKS  # 131072 пикселей

# ===== РАДИУСЫ =====
CHUNK_LOAD_RADIUS = 3  # Загружаем 7x7 чанков (в памяти)
MINIMAP_RADIUS = 1     # На мини-карте 3x3 чанка
COMBAT_RADIUS = CHUNK_SIZE  # Дальность боя = 1 чанк

# ===== НАСТРОЙКИ ГЕНЕРАЦИИ =====
STARS_PER_CHUNK = 200
ASTEROIDS_PER_CHUNK_BASE = 5
ASTEROIDS_PER_CHUNK_MAX = 20
BASES_PER_CHUNK = 1
RESOURCES_PER_CHUNK = 5

# ===== НАСТРОЙКИ ЗВЁЗДНОГО ФОНА (ПАРАЛЛАКС) =====
# Каждый слой: (количество, скорость, мин_размер, макс_размер, мин_яркость, макс_яркость, шанс_цвета)
STAR_LAYERS = [
    # Слой 1: Очень дальние (почти неподвижные, мелкие, тусклые)
    (400, 0.01, 1, 1, 20, 60, 0.1),
    
    # Слой 2: Дальние (медленно, мелкие)
    (300, 0.025, 1, 1, 40, 90, 0.2),
    
    # Слой 3: Средние
    (200, 0.05, 1, 2, 70, 140, 0.4),
    
    # Слой 4: Ближние (быстрее, крупнее)
    (120, 0.09, 2, 3, 120, 200, 0.6),
    
    # Слой 5: Очень близкие (быстро, крупные, яркие)
    (60, 0.15, 2, 4, 180, 255, 0.8),
]

# Радиус генерации звёзд вокруг игрока
STAR_SPAWN_RADIUS_MULTIPLIER = 2  # Множитель от размера экрана

# ===== НАСТРОЙКИ КОРАБЛЯ =====
SHIP_ACCELERATION = 0.2
SHIP_FRICTION = 0.9999
SHIP_MAX_SPEED = 8
SHIP_ROTATION_SPEED = 3
SHIP_RADIUS = 15
SHIP_MAX_HEALTH = 100
SHOOT_DELAY = 10
BULLET_SPEED = 10
BULLET_LIFE = 60
BULLET_RADIUS = 4

# ===== НАСТРОЙКИ ВРАГОВ =====
ENEMY_RADIUS = 40
ENEMY_BASE_SPEED = 1.5
ENEMY_MAX_HEALTH = 3
ENEMY_SHOOT_DELAY_MIN = 30
ENEMY_SHOOT_DELAY_MAX = 90
ENEMY_BULLET_SPEED = 5
ENEMY_SPAWN_DELAY_START = 60
ENEMY_SPAWN_DELAY_MIN = 20

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# ===== НАСТРОЙКИ ЧАСТИЦ =====
EXPLOSION_COUNT = 40  # Количество частиц во взрыве
EXPLOSION_SPEED = 6   # Скорость разлета
TRAIL_COUNT = 5       # Частиц в следе

# ===== НАСТРОЙКИ БОНУСОВ =====
POWERUP_SPAWN_DELAY = 300  # Кадров между спавном (300 = 5 секунд)
POWERUP_DROP_CHANCE = 0.3   # Шанс выпадения из врага
POWERUP_LIFETIME = 600      # Кадров жизни бонуса (600 = 10 секунд)

# ===== НАСТРОЙКИ ВРАГОВ =====
ENEMY_TYPES_WEIGHTS = {
    'scout': 30,
    'tank': 15,
    'sniper': 10,
    'kamikaze': 8,
    'swarmer': 20,
    'guardian': 5,
    'turret': 5
}

# ===== НАСТРОЙКИ ГРАФИКИ =====
PARTICLE_DENSITY = 1.0
STAR_DENSITY = 1.0
SHOW_HEALTH_BARS = True

# ===== НАСТРОЙКИ ВОЛН =====
WAVE_ENEMY_COUNT = 5  # Базовое количество врагов в волне
WAVE_ENEMY_INCREASE = 2  # На сколько врагов больше с каждой волной
WAVE_PAUSE_DURATION = 180  # Пауза между волнами (в кадрах = 3 секунды)
WAVE_MAX_ENEMIES = 30  # Максимум врагов в волне
WAVE_SPAWN_DELAY_BASE = 30  # Задержка между спавном врагов в волне
WAVE_SPAWN_DELAY_MIN = 5  # Минимальная задержка

# ===== НАСТРОЙКИ СПАВНА =====
SPAWN_SAFE_DISTANCE = 300  # Минимальное расстояние от игрока
SPAWN_ENEMY_SEPARATION = 100  # Минимальное расстояние между врагами
SPAWN_FORBIDDEN_ANGLE = 72  # Градусов впереди игрока (запрещённая зона)
SPAWN_ATTEMPTS = 100

# ===== НАСТРОЙКИ ВРАГОВ =====
ENEMY_FAR_DISTANCE = 24000   # Дальше этого — враг удаляется
ENEMY_TELEPORT_DISTANCE = 3000  # Дальше этого и медленный — телепорт

# ===== НАСТРОЙКИ БАЗ =====
BASE_HEALTH = 100
BASE_SPAWN_RATE = 60
BASE_MAX_ENEMIES = 5
BASE_SPAWN_RANGE = 300

DIFFICULTY_SETTINGS = {
    'easy': {
        'enemy_health_multiplier': 0.5,
        'enemy_speed_multiplier': 0.8,
        'enemy_spawn_rate': 0.7,
        'player_damage_multiplier': 0.5,
        'player_health_multiplier': 1.5,
        'score_multiplier': 0.8,
    },
    'normal': {
        'enemy_health_multiplier': 1.0,
        'enemy_speed_multiplier': 1.0,
        'enemy_spawn_rate': 1.0,
        'player_damage_multiplier': 1.0,
        'player_health_multiplier': 1.0,
        'score_multiplier': 1.0,
    },
    'hard': {
        'enemy_health_multiplier': 1.5,
        'enemy_speed_multiplier': 1.2,
        'enemy_spawn_rate': 1.5,
        'player_damage_multiplier': 1.5,
        'player_health_multiplier': 0.7,
        'score_multiplier': 1.3,
    }
}

# ===== РЕСУРСЫ =====
RESOURCE_TYPES = ['scrap', 'crystal', 'fuel']
RESOURCE_COLORS = {
    'scrap': (150, 150, 150),
    'crystal': (100, 200, 255),
    'fuel': (255, 200, 50),
}
RESOURCE_ICONS = {
    'scrap': '🔩',
    'crystal': '💎',
    'fuel': '⛽',
}
