# core/game.py
import pygame
import sys
import math
import random
from settings import *
from config_manager import ConfigManager
from entities.ship import Ship
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.powerups import PowerUpSystem
from systems.particles import ParticleSystem
from systems.minimap import Minimap
from world.starfield_background import BackgroundStars
from world.chunk_manager import ChunkManager
from core.camera import Camera
from utils import check_collision, distance_between, spawn_position
from systems.direction_indicators import DirectionIndicators
from entities.enemy_manager import EnemyManager
from entities.base import EnemyBase
from entities.player_base import PlayerBase
from systems.fuel import FuelSystem
from entities.asteroid import Asteroid
from entities.outpost import Outpost
from systems.world_map import WorldMap
from systems.waypoints import Waypoint, WaypointManager
from systems.spatial_grid import SpatialGrid
from systems.sprite_manager import SpriteManager

# Инициализация шрифтов (глобально для HUD)
pygame.font.init()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 20)


class Game:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.paused = False

        # ===== МЕНЕДЖЕР СПРАЙТОВ =====
        self.sprite_manager = SpriteManager()
        
        # ===== ЗВЁЗДЫ (ФОН) =====
        self.starfield = BackgroundStars()

        # ===== МАРКЕРЫ =====
        self.waypoint_manager = WaypointManager()
        
        # ===== БОЛЬШАЯ КАРТА =====
        self.world_map = WorldMap(self.screen, config, self.waypoint_manager)  # <-- ПЕРЕДАЁМ
               
        # ===== МИР И ЧАНКИ =====
        self.chunk_manager = ChunkManager()

        # ===== КОРАБЛЬ =====
        self.ship = Ship(0, 0, self.sprite_manager)
        self.ship.max_speed = self.ship.normal_max_speed
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)

        # ===== ИГРОВЫЕ СИСТЕМЫ =====
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.minimap = Minimap(self.screen, config)
        self.indicators = DirectionIndicators()

        # ===== РЕСУРСЫ =====
        self.resources = {
            'scrap': 0,
            'crystal': 0,
            'fuel': 0,
        }
        
        # ===== АВАНПОСТЫ =====
        self.outposts = []
        
        # ===== АНГАР =====
        self.hangar = None
        self.hangar_not_available = False
        self.hangar_not_available_timer = 0
        
        # Сохраняем выбранные детали для ангара (между открытиями)
        self.hangar_state = {
            'current_parts': {
                'ships': 'player_base',
                'weapons': 'weapon_static',
                'engines': 'engine_small',
                'shields': 'shield_basic'
            },
            'selected_indices': {
                'ships': 0,
                'weapons': 0,
                'engines': 0,
                'shields': 0
            }
        }
        
        # ===== ПРОСТРАНСТВЕННАЯ СЕТКА ДЛЯ КОЛЛИЗИЙ =====
        from systems.spatial_grid import SpatialGrid
        self.spatial_grid = SpatialGrid(cell_size=300)
        
        # ===== СЛОЖНОСТЬ =====
        self.difficulty = config.get('game.difficulty', 'normal')
        self._apply_difficulty()
        
        # ===== МЕНЕДЖЕР ВРАГОВ =====
        self.enemy_manager = EnemyManager()

        # ===== СПИСКИ ОБЪЕКТОВ =====
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []      # <-- ДОБАВИТЬ
        self.enemy_bases = []

        # ===== БАЗА ИГРОКА =====
        from utils import spawn_position_with_safety
        
        bx, by = spawn_position_with_safety(0, 0, 0, 0, min_distance=500)
        self.player_base = PlayerBase(bx, by)
        
        # ===== ПРИНУДИТЕЛЬНАЯ ЗАГРУЗКА ЧАНКОВ =====
        self.chunks_loaded = False
        
        # Загружаем чанки вокруг игрока
        self.chunk_manager.update(self.ship.x, self.ship.y)
        
        # Загружаем базы из всех загруженных чанков
        self._force_load_chunk_objects()
        self.chunks_loaded = True
        
        # ===== ЕСЛИ НЕТ БАЗ - СОЗДАЁМ ТЕСТОВУЮ =====
        if len(self.enemy_bases) == 0:
            test_base = EnemyBase(
                self.ship.x + 800,
                self.ship.y + 800,
                'standard'
            )
            self.enemy_bases.append(test_base)

        # ===== НАЧАЛЬНЫЕ ОБЪЕКТЫ (если чанки пустые) =====
        if len(self.asteroids) < 10:
            self._init_asteroids()
            
        # ===== ИГРОВЫЕ ПЕРЕМЕННЫЕ =====
        self.score = 0
        self.keys = pygame.key.get_pressed()
        self.mouse_pressed = False

        # ===== ТОПЛИВО =====
        self.fuel_system = FuelSystem(max_fuel=100)

        # ============================================================
        #  ОБРАБОТКА СОБЫТИЙ
        # ============================================================

    def handle_events(self):
        """Обработка событий"""
        # ===== АНГАР =====
        if self.hangar is not None and self.hangar.active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._save_modified_chunks()
                    self._save_player_chunk()
                    self.running = False
                    return "quit"
                
                self.hangar.handle_event(event)
                
                if not self.hangar.active:
                    self.hangar = None
                    self.paused = False
            
            return None
        
        # ===== ОСТАЛЬНЫЕ СОБЫТИЯ =====
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_modified_chunks()
                self._save_player_chunk()
                self.running = False
                return "quit"
            
            # TAB - переключение карты
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.world_map.toggle()
                if self.world_map.visible:
                    self.paused = True
                else:
                    self.paused = False
                continue
            
            # Передаём события карте
            self.world_map.handle_events(event)
            
            # Если карта видна - не обрабатываем другие события
            if self.world_map.visible:
                continue
            
            # Остальные события
            if event.type == pygame.KEYDOWN:
                # Чит-коды (только в режиме отладки)
                
                # Стандартные клавиши
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self._restart()
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"
                else:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_h:
                        self._open_hangar()
            
            # Клик мыши для стрельбы
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_pressed = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Вверх — приближение
                    self.camera.zoom_in()
                elif event.button == 5:  # Вниз — отдаление
                    self.camera.zoom_out()
                    
        return None
        
    def _handle_cheats(self, event):
        """Обработка чит-кодов"""
        if not self.config.get('game.debug_mode', False):
            return
        
        if event.key == pygame.K_F1:
            self._activate_bomb()
            print("[CHEAT] 💥 Bomb activated!")
        elif event.key == pygame.K_F2:
            self.ship.health = self.ship.max_health
            print("[CHEAT] ❤️ Health restored!")
        elif event.key == pygame.K_F3:
            self.score += 50
            print(f"[CHEAT] ⭐ +50 points! Score: {self.score}")
        elif event.key == pygame.K_F4:
            for enemy in self.enemies[:]:
                enemy.destroy(self.particles)
                self.score += enemy.score_value
                self.enemies.remove(enemy)
            print(f"[CHEAT] 👾 All enemies killed! Score: {self.score}")
        elif event.key == pygame.K_F5:
            for _ in range(5):
                self._spawn_enemy()
            print("[CHEAT] 🌀 Spawned 5 enemies!")
        elif event.key == pygame.K_F6:
            print("[CHEAT] 🔄 Принудительная загрузка баз из файлов...")
            self._force_load_chunk_objects()
            print(f"[CHEAT] ✅ Загружено баз: {len(self.enemy_bases)}")
        elif event.key == pygame.K_F7:
            print("[CHEAT] 🧹 Принудительная очистка файлов...")
            for chunk in self.chunk_manager.chunks.values():
                if chunk.loaded:
                    bases = chunk.objects.get('enemy_bases', [])
                    chunk.objects['enemy_bases'] = [b for b in bases if b.get('health', 0) > 0]
                    chunk.modified = True
                    chunk.save(self.chunk_manager.world_dir)
            print("[CHEAT] ✅ Очистка завершена!")
        elif event.key == pygame.K_F8:
            # НАГРУЗОЧНЫЙ ТЕСТ
            self._run_load_test()
        elif event.key == pygame.K_F9:
            self._run_render_test()
        elif event.key == pygame.K_F10:  # F10
            self._run_real_test()
            
    # ============================================================
    #  УПРАВЛЕНИЕ
    # ============================================================

    def _handle_controls(self):
        keys = self.keys
        has_fuel = self.fuel_system.has_fuel()
        
        # Поворот
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship.rotate_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship.rotate_right()
        
        # Тяга
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and has_fuel:
            self.ship.thrust(True)
        else:
            self.ship.stop_thrust()
        
        # ===== МИРОВЫЕ КООРДИНАТЫ МЫШКИ =====
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x, world_mouse_y = self.camera.screen_to_world(mouse_x, mouse_y)
        
        # Наводим турели на мышку
        self.ship.aim_weapons(world_mouse_x, world_mouse_y)
        
        # Стрельба
        if keys[pygame.K_SPACE]:
            self.ship.shoot(self.bullets, world_mouse_x, world_mouse_y)
        
        if self.mouse_pressed:
            self.ship.shoot(self.bullets, world_mouse_x, world_mouse_y)
        
        # Варп
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and has_fuel:
            if self.fuel_system.activate_warp():
                self.ship.set_warp(True)
        else:
            if self.fuel_system.warp_active:
                self.fuel_system.deactivate_warp()
                self.ship.set_warp(False)
        
        # Взаимодействие с аванпостом
        if keys[pygame.K_e]:
            self._interact_with_nearby_outpost()
        
        # Ангар
        if keys[pygame.K_h]:
            if self.is_near_base():
                self._open_hangar()
            else:
                self.hangar_not_available = True
                self.hangar_not_available_timer = 120
            
    # ============================================================
    #  ИГРОВЫЕ МЕХАНИКИ
    # ============================================================

    def _init_bases(self):
        """Создаёт начальные ульи с проверкой расстояний"""
        from utils import spawn_position_with_safety

        for _ in range(random.randint(3, 5)):
            x, y = spawn_position_with_safety(
                self.ship.x,
                self.ship.y,
                self.ship.speed_x,
                self.ship.speed_y,
                min_distance=800,
                max_attempts=50,
                existing_bases=self.enemy_bases,  # Проверяем другие базы
                base_separation=600               # Минимум 600 между базами
            )
            base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
            base = EnemyBase(x, y, base_type)
            self.enemy_bases.append(base)
            print(f"[BASE] Улей типа {base_type} создан в ({int(x)}, {int(y)}) с {base.max_enemies} врагами")
            
    def _init_bases_from_chunks(self):
        """Создаёт базы из чанков и соединяет их в комплексы"""
        from entities.base import EnemyBase
        
        # Получаем все базы из чанков
        all_bases = []
        for chunk in self.chunk_manager.chunks.values():
            if chunk.loaded:
                for base_data in chunk.objects.get('enemy_bases', []):
                    base = EnemyBase(
                        base_data['x'], 
                        base_data['y'], 
                        base_data.get('base_type', 'standard')
                    )
                    base.health = base_data.get('health', 100)
                    base.max_health = base_data.get('max_health', 100)
                    base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                    all_bases.append(base)
        
        # Соединяем близкие базы в комплексы
        complexes = []
        used = set()
        
        for i, base1 in enumerate(all_bases):
            if i in used:
                continue
            
            complex_bases = [base1]
            used.add(i)
            
            # Ищем соседей для соединения
            for j, base2 in enumerate(all_bases):
                if j in used:
                    continue
                
                dist = math.sqrt((base1.x - base2.x)**2 + (base1.y - base2.y)**2)
                if dist < base1.connection_distance * 1.2:
                    base1.connect_to(base2)
                    complex_bases.append(base2)
                    used.add(j)
            
            complexes.append(complex_bases)
        
        # Добавляем все базы в игру
        for base in all_bases:
            self.enemy_bases.append(base)
        
        print(f"[BASE] Создано {len(all_bases)} баз, {len(complexes)} комплексов")
        for i, complex_bases in enumerate(complexes):
            print(f"  Комплекс {i+1}: {len(complex_bases)} баз")
            
    def _connect_bases_into_complexes(self):
        """Соединяет близкие базы в комплексы (при загрузке)"""
        
        if len(self.enemy_bases) < 2:
            return
        
        # Сбрасываем старые связи
        for base in self.enemy_bases:
            base.parent = None
            base.children = []
            base.connected = False
        
        # Группируем базы по типу
        bases_by_type = {}
        for base in self.enemy_bases:
            if base.base_type not in bases_by_type:
                bases_by_type[base.base_type] = []
            bases_by_type[base.base_type].append(base)
        
        complexes = 0
        
        for base_type, bases in bases_by_type.items():
            if len(bases) < 2:
                continue
            
            # Сортируем по близости к центру
            bases.sort(key=lambda b: abs(b.x) + abs(b.y))
            
            used = set()
            for i, base1 in enumerate(bases):
                if i in used:
                    continue
                
                complex_bases = [base1]
                used.add(i)
                
                for j, base2 in enumerate(bases):
                    if j in used:
                        continue
                    
                    # Проверяем расстояние до любой базы в комплексе
                    is_near = False
                    for comp_base in complex_bases:
                        dist = math.sqrt((comp_base.x - base2.x)**2 + (comp_base.y - base2.y)**2)
                        if dist < base1.connection_distance * 1.3:
                            is_near = True
                            break
                    
                    if is_near and len(complex_bases) < 7:
                        base1.connect_to(base2)
                        complex_bases.append(base2)
                        used.add(j)
                
                if len(complex_bases) > 1:
                    complexes += 1
                    # Усиливаем главную базу
                    base1.max_health = 100 + len(complex_bases) * 20
                    base1.health = base1.max_health
                    base1.max_enemies = 6 + len(complex_bases) * 2
                    base1.current_enemies = base1.max_enemies
                    base1.radius = 45 + len(complex_bases) * 3
                    
    def _init_asteroids(self):
        """Создаёт начальные астероиды"""
        for _ in range(15):
            x = random.randint(-2000, 2000)
            y = random.randint(-2000, 2000)
            # Не спавним рядом с игроком
            if abs(x) < 500 and abs(y) < 500:
                continue
            self.asteroids.append(Asteroid(x, y))
            
    def _force_load_base_from_file(self, chunk_x, chunk_y):
        """Прямая загрузка базы из файла чанка"""
        from entities.base import EnemyBase
        import json
        import os
        
        chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
        filename = chunk.get_full_path(self.chunk_manager.world_dir)
        
        if not os.path.exists(filename):
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bases = data.get('objects', {}).get('enemy_bases', [])
                
                if not bases:
                    return False
                
                loaded = 0
                for base_data in bases:
                    # Проверяем, загружена ли уже эта база
                    exists = False
                    for existing in self.enemy_bases:
                        if abs(existing.x - base_data['x']) < 10 and abs(existing.y - base_data['y']) < 10:
                            exists = True
                            break
                    
                    if not exists:
                        base = EnemyBase(
                            base_data['x'],
                            base_data['y'],
                            base_data.get('base_type', 'standard')
                        )
                        base.health = base_data.get('health', 100)
                        base.max_health = base_data.get('max_health', 100)
                        base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                        self.enemy_bases.append(base)
                        loaded += 1
                
                return True
                
        except Exception as e:
            return False

    def _force_load_chunk_objects(self):
        """Принудительно загружает все объекты из загруженных чанков"""
        from entities.base import EnemyBase
        from entities.asteroid import Asteroid
        from entities.outpost import Outpost
                
        # Перезагружаем все чанки из файлов
        for key, chunk in list(self.chunk_manager.chunks.items()):
            if chunk.loaded:
                chunk.load(self.chunk_manager.world_dir)
        
        # Очищаем старые объекты
        self.enemy_bases.clear()
        self.asteroids.clear()
        self.outposts.clear()
        
        # Загружаем базы
        for chunk in self.chunk_manager.chunks.values():
            if not chunk.loaded:
                continue
            
            for base_data in chunk.objects.get('enemy_bases', []):
                base = EnemyBase(
                    base_data['x'], 
                    base_data['y'], 
                    base_data.get('base_type', 'standard')
                )
                base.health = base_data.get('health', 100)
                base.max_health = base_data.get('max_health', 100)
                base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                base.unique_id = base_data.get('unique_id', f"{int(base_data['x'])}_{int(base_data['y'])}_{base.base_type}")
                self.enemy_bases.append(base)
            
            for ast_data in chunk.objects.get('asteroids', []):
                asteroid = Asteroid(
                    ast_data['x'], 
                    ast_data['y'],
                    ast_data.get('radius'),
                    ast_data.get('health')
                )
                self.asteroids.append(asteroid)
            
            # ===== ЗАГРУЖАЕМ АВАНПОСТЫ =====
            for outpost_data in chunk.objects.get('outposts', []):
                outpost = Outpost(
                    outpost_data['x'], 
                    outpost_data['y'], 
                    outpost_data.get('outpost_type', 'trade')
                )
                outpost.resources = outpost_data.get('resources', {'scrap': 100, 'crystal': 20, 'fuel': 50})
                outpost.missions = outpost_data.get('missions', [])
                self.outposts.append(outpost)
        
        # Соединяем базы в комплексы
        if len(self.enemy_bases) > 1:
            self._connect_bases_into_complexes()

    def spawn_enemy(self, x, y, enemy_type=None, difficulty_multiplier=1.0):
        """Создаёт врага указанного типа"""
        if enemy_type is None:
            enemy_type = self.get_random_type()
        
        if enemy_type not in self.enemy_types:
            print(f"[ENEMY_MANAGER] Ошибка: тип '{enemy_type}' не найден")
            return None
        
        enemy = Enemy(x, y, enemy_type, difficulty_multiplier)
        return enemy
        
    def _spawn_enemy_with_base(self, x, y, enemy_type, base_color=None):
        """Создаёт врага для базы с цветом"""
        enemy = self.enemy_manager.spawn_enemy(
            x, y, enemy_type,
            self.sprite_manager,
            self.difficulty_multiplier,
            base_color  # <-- ЦВЕТ ОТ БАЗЫ
        )
        if enemy:
            self.enemies.append(enemy)
        return enemy
    
    def _activate_bomb(self):
        """Активирует бомбу"""
        for enemy in self.enemies[:]:
            enemy.destroy(self.particles)
            self.score += enemy.score_value
            self.enemies.remove(enemy)

        self.particles.spawn_explosion(
            self.ship.x, self.ship.y,
            count=100,
            speed=10,
            colors=[(255, 200, 50), (255, 100, 50), (255, 255, 255)]
        )
        self.powerups.active_effects['bomb'] = 1

    def _interact_with_nearby_outpost(self):
        """Взаимодействие с ближайшим аванпостом"""
        nearest_outpost = None
        nearest_dist = 200
        
        for outpost in self.outposts:
            if not outpost.alive:
                continue
            dist = math.sqrt((outpost.x - self.ship.x)**2 + (outpost.y - self.ship.y)**2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_outpost = outpost
        
        if nearest_outpost:
            # Показываем меню в консоли
            result = nearest_outpost.interact(self.ship, self)
            
            # Если это торговля - ждём ввода
            if result == 'trade':
                self._handle_trade_input(nearest_outpost)
    
    def _handle_trade_input(self, outpost):
        """Обработка ввода для торговли"""
        # Временно используем консольный ввод
        # Позже можно сделать GUI меню
        try:
            choice = int(input("Выберите пункт (1-6): "))
            outpost.trade(self, choice)
        except ValueError:
            print("❌ Неверный ввод!")

    def _open_hangar(self):
        """Открывает ангар"""
        if not self.is_near_base():
            print("[HANGAR] ОШИБКА: попытка открыть ангар не на базе!")
            return
    
        from ui.hangar import Hangar
        # Передаём сохранённое состояние
        self.hangar = Hangar(
            self.screen, 
            self.ship, 
            self.sprite_manager,
            self.hangar_state  # <-- передаём состояние
        )
        self.paused = True
        
    def _apply_difficulty(self):
        """Применяет настройки сложности"""
        if self.difficulty == 'easy':
            self.difficulty_multiplier = 0.5
            self.enemy_spawn_modifier = 0.7
            self.damage_modifier = 0.5
            self.health_modifier = 1.5
            print("[DIFFICULTY] Легкая сложность")
        elif self.difficulty == 'normal':
            self.difficulty_multiplier = 1.0
            self.enemy_spawn_modifier = 1.0
            self.damage_modifier = 1.0
            self.health_modifier = 1.0
            print("[DIFFICULTY] Нормальная сложность")
        elif self.difficulty == 'hard':
            self.difficulty_multiplier = 1.5
            self.enemy_spawn_modifier = 1.5
            self.damage_modifier = 1.5
            self.health_modifier = 0.7
            print("[DIFFICULTY] Сложная сложность")
        else:
            self.difficulty_multiplier = 1.0
            self.enemy_spawn_modifier = 1.0
            self.damage_modifier = 1.0
            self.health_modifier = 1.0
            
    def _restart(self):
        """Перезапуск игры"""
        self.game_over = False
        self.score = 0
        self.ship = Ship(0, 0)
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []
        self.enemy_bases = []
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)
        
        # Пересоздаём чанки и загружаем объекты
        self.chunk_manager = ChunkManager(config=self.config)
        self._force_load_chunk_objects()
        
        # Пересоздаём базу игрока
        from utils import spawn_position_with_safety
        bx, by = spawn_position_with_safety(0, 0, 0, 0, min_distance=500)
        self.player_base = PlayerBase(bx, by)
        
    # ============================================================
    #  ОБНОВЛЕНИЕ
    # ============================================================

    def update(self):
        # Если карта открыта - обновляем только чанки (для фона)
        if self.world_map.visible:
            # Обновляем чанки чтобы карта показывала актуальные данные
            self.chunk_manager.update(self.ship.x, self.ship.y)
            return
        
        if self.paused or self.game_over:
            return
            
        # Управление
        self.keys = pygame.key.get_pressed()
        self._handle_controls()

        # Сохраняем старую позицию для параллакса
        old_x, old_y = self.ship.x, self.ship.y

        # Обновление корабля
        self.ship.update()

        # Смещение для параллакса
        offset_x = -(self.ship.x - old_x)
        offset_y = -(self.ship.y - old_y)

        # Обновление звёзд
        self.starfield.update(self.ship.x, self.ship.y, offset_x, offset_y)

        # Варп эффект для звёзд
        if self.fuel_system.warp_active:
            self.starfield.set_warp(True)
        else:
            self.starfield.set_warp(False)
            
        # ===== ОБНОВЛЕНИЕ ЧАНКОВ =====
        old_chunk_x = int(self.ship.x // CHUNK_SIZE)
        old_chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        new_chunk_x = int(self.ship.x // CHUNK_SIZE)
        new_chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        self.chunk_manager.update(self.ship.x, self.ship.y)
        
        # При переходе в новый чанк - перезагружаем объекты
        if old_chunk_x != new_chunk_x or old_chunk_y != new_chunk_y:
            self._force_load_chunk_objects()
        
        # Обновление баз врагов
        for base in self.enemy_bases[:]:
            base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)

        # ===== КАЖДЫЕ 5 СЕКУНД ПРОВЕРЯЕМ ЧТО БАЗЫ ЕСТЬ =====
        if len(self.enemy_bases) < 2 and pygame.time.get_ticks() % 300 == 0:
            print(f"[GAME] Баз мало ({len(self.enemy_bases)}), загрузка...")
            self._force_load_chunk_objects()
        
        # ===== ДИНАМИЧЕСКАЯ ПРОВЕРКА КОМПЛЕКСОВ (каждые 3 секунды) =====
        if pygame.time.get_ticks() % 180 == 0:
            # Проверяем, не появились ли новые базы рядом
            for base in self.enemy_bases:
                if base.parent is None and base.children:
                    # У базы уже есть дети - всё ок
                    continue
                
                # Ищем соседей для новых баз
                for other in self.enemy_bases:
                    if other == base or other.parent is not None:
                        continue
                    
                    dist = math.sqrt((base.x - other.x)**2 + (base.y - other.y)**2)
                    if dist < base.connection_distance * 1.3:
                        # Нашли соседа - соединяем
                        if base.parent is None:
                            # Создаём новый комплекс
                            base.connect_to(other)
                            base.max_health = 120
                            base.health = 120
                            base.max_enemies = 8
                            base.current_enemies = 8
                        else:
                            # Присоединяем к существующему комплексу
                            base.parent.connect_to(other)
                            
        # Обновление базы игрока
        self.player_base.update(self.ship, self.particles)

        # Обновление частиц и бонусов
        self.particles.update()
        self.powerups.update(self.ship.x, self.ship.y)

        # Обновление пуль
        self._update_bullets()

        # Управление врагами
        self._update_enemies()

        # Управление вражескими пулями
        self._update_enemy_bullets()

        # Проверка попаданий по базам
        self._check_base_hits()

        # Сбор бонусов
        self.powerups.check_collection(self.ship, self.particles)

        # Обработка бомбы
        if 'bomb' in self.powerups.active_effects:
            self._activate_bomb()
            del self.powerups.active_effects['bomb']

        # Обновление эффектов на корабле
        self.powerups.update_effects(self.ship)

        # Обновление указателей направления
        self.indicators.update(
            self.ship.x,
            self.ship.y,
            self.enemies,
            self.camera.x,
            self.camera.y,
            self.enemy_bases
        )

        # Таймер сообщения об ангаре
        if self.hangar_not_available_timer > 0:
            self.hangar_not_available_timer -= 1
            if self.hangar_not_available_timer == 0:
                self.hangar_not_available = False
                
        # ===== КОЛЛИЗИИ =====
        self._check_all_collisions()

        # Обновление топлива
        self.fuel_system.update(
            self.ship,
            self.ship.engine_on,
            self.particles
        )
        
    # ============================================================
    #  ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ UPDATE
    # ============================================================

    def _update_bullets(self):
        """Обновление пуль игрока"""
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_dead():
                self.bullets.remove(bullet)

    def _update_enemy_bullets(self):
        """Обновление вражеских пуль"""
        for bullet in self.enemy_bullets[:]:
            bullet.update()
            
            # Если пуля умерла — удаляем и пропускаем
            if bullet.is_dead():
                self.enemy_bullets.remove(bullet)
                continue
            
            # Проверка попадания в игрока
            if not check_collision(bullet, self.ship, -5):
                continue
            
            # Попадание!
            if 'shield' in self.powerups.active_effects:
                self.enemy_bullets.remove(bullet)
                self.particles.spawn_explosion(
                    bullet.x, bullet.y, 10, 3,
                    [(50, 150, 255), (255, 255, 255)]
                )
                continue

            self.ship.health -= 5
            self.enemy_bullets.remove(bullet)
            self.particles.spawn_explosion(
                bullet.x, bullet.y, 10, 3,
                [(255, 200, 100), (255, 255, 255)]
            )

            if self.ship.health <= 0:
                self.game_over = True
                
    def _update_enemies(self):
        """Обновление всех врагов"""
        for enemy in self.enemies[:]:
            enemy.update(self.ship.x, self.ship.y)
            enemy.shoot(self.enemy_bullets, self.ship.x, self.ship.y)

            # Проверка столкновения с кораблём
            if check_collision(self.ship, enemy, -5):
                self.ship.health -= 10
                enemy.destroy(self.particles)
                self.enemies.remove(enemy)
                if self.ship.health <= 0:
                    self.game_over = True
                continue

            # Камикадзе взрыв
            if enemy.behavior == 'kamikaze' and enemy.is_exploding:
                dist = distance_between(self.ship.x, self.ship.y, enemy.x, enemy.y)
                if dist < enemy.explosion_radius:
                    self.ship.health -= 30
                    enemy.destroy(self.particles)
                    self.enemies.remove(enemy)
                    if self.ship.health <= 0:
                        self.game_over = True
                continue

            # Попадания пуль во врага
            for bullet in self.bullets[:]:
                if check_collision(bullet, enemy):
                    if enemy.take_damage():
                        enemy.destroy(self.particles)
                        self.powerups.spawn_from_enemy(enemy.x, enemy.y, 0.3)
                        self.score += enemy.score_value
                        self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    break

        # Удаление "застрявших" врагов
        self._cleanup_far_enemies()

    def _cleanup_far_enemies(self):
        """Удаляет или телепортирует врагов, улетевших слишком далеко"""
        for enemy in self.enemies[:]:
            dx = enemy.x - self.ship.x
            dy = enemy.y - self.ship.y
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 8000:
                print(f"[ENEMY] Удалён далёкий враг {enemy.enemy_type} на расстоянии {int(dist)}")
                self.enemies.remove(enemy)
                self.score += enemy.score_value // 2
                continue

            speed = math.sqrt(enemy.speed_x**2 + enemy.speed_y**2)
            if dist > 3000 and speed < 0.1:
                from utils import spawn_position_with_safety
                x, y = spawn_position_with_safety(
                    self.ship.x,
                    self.ship.y,
                    self.ship.speed_x,
                    self.ship.speed_y,
                    min_distance=400
                )
                enemy.x = x
                enemy.y = y
                print(f"[ENEMY] Телепорт застрявшего врага {enemy.enemy_type}")
    
    def _check_base_hits(self):
        """Проверка попаданий по базам"""
        for bullet in self.bullets[:]:
            for base in self.enemy_bases[:]:
                if not base.alive:
                    continue

                dx = bullet.x - base.x
                dy = bullet.y - base.y
                dist = math.sqrt(dx**2 + dy**2)

                if dist < base.radius + bullet.radius:
                    base.take_damage(
                        self.enemies, 
                        1, 
                        self.chunk_manager,
                        self._save_modified_chunks
                    )
                    self.bullets.remove(bullet)

                    self.particles.spawn_explosion(
                        bullet.x, bullet.y,
                        count=5,
                        speed=2,
                        colors=[(255, 200, 100), (255, 255, 255)]
                    )

                    if not base.alive:
                        self.score += 50
                        self.particles.spawn_explosion(
                            base.x, base.y,
                            count=60,
                            speed=8,
                            colors=[(255, 50, 50), (255, 200, 50), (255, 255, 255)]
                        )
                        
                        # ДОПОЛНИТЕЛЬНО СОХРАНЯЕМ ЧАНК ИГРОКА
                        self._save_player_chunk()
                        
                        print(f"[BASE] База уничтожена! +50 очков")

                    break
                    
    def _check_asteroid_collision(self, asteroid, obj, margin=0):
        """Проверка столкновения с астероидом"""
        dx = asteroid.x - obj.x
        dy = asteroid.y - obj.y
        dist = math.sqrt(dx**2 + dy**2)
        return dist < (asteroid.radius + obj.radius + margin)

    def _check_all_collisions(self):
        """Проверяет все коллизии с использованием пространственной сетки"""
        from utils import circle_collision, circle_polygon_collision, resolve_collision
        
        # ===== ОБНОВЛЯЕМ ПРОСТРАНСТВЕННУЮ СЕТКУ =====
        self.spatial_grid.clear()
        
        # Добавляем все объекты
        for enemy in self.enemies:
            if enemy.health > 0:
                self.spatial_grid.add(enemy)
        
        for base in self.enemy_bases:
            if base.alive:
                self.spatial_grid.add(base)
        
        for asteroid in self.asteroids:
            self.spatial_grid.add(asteroid)
        
        for bullet in self.bullets:
            self.spatial_grid.add_bullet(bullet)
        
        for bullet in self.enemy_bullets:
            self.spatial_grid.add_bullet(bullet)
        
        # ===== 1. ПУЛИ ИГРОКА VS ВРАГИ =====
        for bullet in self.bullets[:]:
            if bullet.is_dead():
                continue
            
            # Находим потенциальные цели
            potential_targets = self.spatial_grid.get_nearby(bullet)
            
            for enemy in potential_targets:
                if enemy not in self.enemies or enemy.health <= 0:
                    continue
                
                if circle_collision(bullet, enemy):
                    enemy.health -= bullet.damage
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 255, 100), (255, 200, 50)]
                    )
                    
                    if enemy.health <= 0:
                        enemy.destroy(self.particles)
                        self.powerups.spawn_from_enemy(enemy.x, enemy.y, 0.3)
                        self.score += enemy.score_value
                        self.enemies.remove(enemy)
                        self.spatial_grid.remove(enemy)
                    break
        
        # ===== 2. ПУЛИ ИГРОКА VS БАЗЫ =====
        for bullet in self.bullets[:]:
            if bullet.is_dead():
                continue
            
            potential_targets = self.spatial_grid.get_nearby(bullet)
            
            for base in potential_targets:
                if base not in self.enemy_bases or not base.alive:
                    continue
                
                if circle_collision(bullet, base):
                    base.take_damage(
                        self.enemies, 
                        1, 
                        self.chunk_manager,
                        self._save_modified_chunks
                    )
                    base.hit_flash = 10
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 200, 100), (255, 255, 255)]
                    )
                    
                    if not base.alive:
                        self.score += 50
                        self.particles.spawn_explosion(
                            base.x, base.y, 60, 8,
                            [(255, 50, 50), (255, 200, 50), (255, 255, 255)]
                        )
                        self._save_modified_chunks()
                        self.spatial_grid.remove(base)
                    break
        
        # ===== 3. ПУЛИ ИГРОКА VS АСТЕРОИДЫ =====
        for bullet in self.bullets[:]:
            if bullet.is_dead():
                continue
            
            potential_targets = self.spatial_grid.get_nearby(bullet)
            
            for asteroid in potential_targets:
                if asteroid not in self.asteroids:
                    continue
                
                if circle_polygon_collision(bullet, asteroid.get_vertices()):
                    asteroid.health -= 1
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 3, 1,
                        [(150, 130, 100), (200, 180, 150)]
                    )
                    
                    if asteroid.health <= 0:
                        resources = asteroid.destroy(self.particles)
                        # Добавляем ресурсы в инвентарь
                        if resources and isinstance(resources, dict):
                            res_type = resources.get('type', 'scrap')
                            amount = resources.get('amount', 0)
                            self.resources[res_type] = self.resources.get(res_type, 0) + amount
                        
                        self.asteroids.remove(asteroid)
                        self.spatial_grid.remove(asteroid)
                        self.score += 5
                    break
                    
        # ===== 4. КОРАБЛЬ VS ВСЕ ОБЪЕКТЫ =====
        # Проверяем только ближайшие объекты
        ship_nearby = self.spatial_grid.get_nearby(self.ship)
        
        for obj in ship_nearby:
            # Враги
            if obj in self.enemies and obj.health > 0:
                if circle_polygon_collision(obj, self.ship.get_vertices(), -5):
                    self._handle_ship_enemy_collision(obj)
            
            # Астероиды
            elif obj in self.asteroids:
                if circle_polygon_collision(obj, self.ship.get_vertices(), -5):
                    self._handle_ship_asteroid_collision(obj)
            
            # Базы
            elif obj in self.enemy_bases and obj.alive:
                if circle_collision(self.ship, obj, -10):
                    self._handle_ship_base_collision(obj)
        
        # ===== 5. ВРАЖЕСКИЕ ПУЛИ VS КОРАБЛЬ =====
        for bullet in self.enemy_bullets[:]:
            if bullet.is_dead():
                continue
            
            # Проверяем только если пуля близко к кораблю
            if abs(bullet.x - self.ship.x) < 200 and abs(bullet.y - self.ship.y) < 200:
                if circle_polygon_collision(bullet, self.ship.get_vertices(), -5):
                    self._handle_enemy_bullet_ship_collision(bullet)
        
        # ===== 6. ВРАЖЕСКИЕ ПУЛИ VS ПУЛИ ИГРОКА =====
        # Быстрая проверка (пропускаем если далеко)
        for bullet in self.bullets[:]:
            if bullet.is_dead():
                continue
            
            potential_targets = self.spatial_grid.get_nearby(bullet)
            
            for enemy_bullet in potential_targets:
                if enemy_bullet not in self.enemy_bullets or enemy_bullet.is_dead():
                    continue
                
                if circle_collision(bullet, enemy_bullet):
                    self.bullets.remove(bullet)
                    self.enemy_bullets.remove(enemy_bullet)
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 255, 255), (200, 200, 200)]
                    )
                    self.spatial_grid.remove(bullet)
                    self.spatial_grid.remove(enemy_bullet)
                    break
        
        # ===== 7. ВРАГИ VS ВРАГИ (только близкие) =====
        for enemy in self.enemies:
            if enemy.health <= 0:
                continue
            
            potential_targets = self.spatial_grid.get_nearby(enemy)
            
            for other in potential_targets:
                if other not in self.enemies or other.health <= 0 or other == enemy:
                    continue
                
                if circle_collision(enemy, other, -5):
                    resolve_collision(enemy, other, 2)
    
    def _handle_ship_enemy_collision(self, enemy):
        """Обработка столкновения корабля с врагом"""
        if 'shield' in self.powerups.active_effects:
            enemy.health -= int(3 * self.damage_modifier)
            if enemy.health <= 0:
                enemy.destroy(self.particles)
                self.score += enemy.score_value
                self.enemies.remove(enemy)
                self.spatial_grid.remove(enemy)
            return
        
        damage = int(10 * self.damage_modifier)
        self.ship.health -= damage
        enemy.health = 0
        enemy.destroy(self.particles)
        self.enemies.remove(enemy)
        self.spatial_grid.remove(enemy)
        
        if self.ship.health <= 0:
            self.game_over = True
    
    def _handle_ship_asteroid_collision(self, asteroid):
        """Обработка столкновения корабля с астероидом"""
        self.ship.health -= 5
        asteroid.health = 0
        
        # Получаем ресурсы с астероида
        resources = asteroid.destroy(self.particles)
        
        # Добавляем ресурсы в инвентарь
        if resources and isinstance(resources, dict):
            res_type = resources.get('type', 'scrap')
            amount = resources.get('amount', 0)
            self.resources[res_type] = self.resources.get(res_type, 0) + amount
        
        self.asteroids.remove(asteroid)
        self.spatial_grid.remove(asteroid)
        
        if self.ship.health <= 0:
            self.game_over = True

    def _handle_ship_base_collision(self, base):
        """Обработка столкновения корабля с базой"""
        if 'shield' in self.powerups.active_effects:
            self.particles.spawn_explosion(
                base.x, base.y, 20, 5,
                [(50, 150, 255), (255, 255, 255)]
            )
            base.take_damage(
                self.enemies, 
                5, 
                self.chunk_manager,
                self._save_modified_chunks
            )
            if not base.alive:
                self.spatial_grid.remove(base)
            return
        
        self.ship.health -= 20
        base.take_damage(
            self.enemies, 
            10, 
            self.chunk_manager,
            self._save_modified_chunks
        )
        
        self.particles.spawn_explosion(
            self.ship.x, self.ship.y, 30, 5,
            [(255, 200, 100), (255, 255, 255)]
        )
        
        if not base.alive:
            self.spatial_grid.remove(base)
            self._save_modified_chunks()
        
        if self.ship.health <= 0:
            self.game_over = True
    
    def _handle_enemy_bullet_ship_collision(self, bullet):
        """Обработка столкновения вражеской пули с кораблём"""
        if 'shield' in self.powerups.active_effects:
            self.particles.spawn_explosion(
                bullet.x, bullet.y, 10, 3,
                [(50, 150, 255), (255, 255, 255)]
            )
            self.enemy_bullets.remove(bullet)
            self.spatial_grid.remove(bullet)
            return
        
        damage = int(5 * self.damage_modifier)
        self.ship.health -= damage
        self.enemy_bullets.remove(bullet)
        self.spatial_grid.remove(bullet)
        self.particles.spawn_explosion(
            bullet.x, bullet.y, 10, 3,
            [(255, 200, 100), (255, 255, 255)]
        )
        
        if self.ship.health <= 0:
            self.game_over = True
            
    def _save_modified_chunks(self):
        """Сохраняет только изменённые чанки"""
        
        saved = self.chunk_manager.save_modified_chunks()
        
        return saved
        
    def _save_player_chunk(self):
        """Сохраняет чанк в котором находится игрок"""
        
        chunk_x = int(self.ship.x // CHUNK_SIZE)
        chunk_y = int(self.ship.y // CHUNK_SIZE)
                
        self.chunk_manager.save_chunk_immediately(chunk_x, chunk_y)

    def _run_load_test(self):
        """Нагрузочный тест: спавн большого количества объектов"""
        import time
        
        print("\n" + "="*50)
        print("🧪 НАГРУЗОЧНЫЙ ТЕСТ")
        print("="*50)
        
        # Спавн врагов
        enemy_counts = [10, 20, 50, 100, 200, 500]
        
        for count in enemy_counts:
            print(f"\n📊 Тест: {count} врагов")
            
            # Спавним врагов
            start_time = time.time()
            for i in range(count):
                x = self.ship.x + random.randint(-2000, 2000)
                y = self.ship.y + random.randint(-2000, 2000)
                enemy_type = random.choice(['scout', 'tank', 'sniper', 'kamikaze', 'swarmer'])
                enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type, self.difficulty_multiplier)
                if enemy:
                    self.enemies.append(enemy)
            
            spawn_time = time.time() - start_time
            print(f"  ⏱️ Спавн: {spawn_time:.3f} сек")
            
            # Проверяем FPS
            fps_start = time.time()
            frame_count = 0
            target_frames = 60
            
            # Делаем несколько кадров для замера
            for _ in range(target_frames):
                # Симулируем обновление (без рендера)
                for enemy in self.enemies[:50]:  # Обновляем только часть для скорости
                    enemy.update(self.ship.x, self.ship.y)
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            print(f"  🎮 FPS: {fps:.1f}")
            
            # Очищаем врагов
            self.enemies.clear()
            print(f"  🧹 Очищено")
        
        # Тест с базами
        print(f"\n📊 Тест: базы")
        base_counts = [5, 10, 20, 50]
        
        for count in base_counts:
            print(f"\n📊 Тест: {count} баз")
            
            # Спавним базы
            start_time = time.time()
            for i in range(count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
                base = EnemyBase(x, y, base_type)
                self.enemy_bases.append(base)
            
            spawn_time = time.time() - start_time
            print(f"  ⏱️ Спавн: {spawn_time:.3f} сек")
            
            # Проверяем FPS
            fps_start = time.time()
            frame_count = 0
            target_frames = 60
            
            for _ in range(target_frames):
                # Симулируем обновление
                for base in self.enemy_bases[:50]:
                    base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            print(f"  🎮 FPS: {fps:.1f}")
            
            # Очищаем базы
            self.enemy_bases.clear()
            print(f"  🧹 Очищено")
        
        # Тест с астероидами
        print(f"\n📊 Тест: астероиды")
        asteroid_counts = [50, 100, 200, 500, 1000]
        
        for count in asteroid_counts:
            print(f"\n📊 Тест: {count} астероидов")
            
            # Спавним астероиды
            start_time = time.time()
            for i in range(count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                asteroid = Asteroid(x, y)
                self.asteroids.append(asteroid)
            
            spawn_time = time.time() - start_time
            print(f"  ⏱️ Спавн: {spawn_time:.3f} сек")
            
            # Проверяем FPS
            fps_start = time.time()
            frame_count = 0
            target_frames = 60
            
            for _ in range(target_frames):
                # Симулируем обновление
                for asteroid in self.asteroids[:50]:
                    asteroid.update()
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            print(f"  🎮 FPS: {fps:.1f}")
            
            # Очищаем астероиды
            self.asteroids.clear()
            print(f"  🧹 Очищено")
        
        # Итог
        print("\n" + "="*50)
        print("✅ НАГРУЗОЧНЫЙ ТЕСТ ЗАВЕРШЁН")
        print("="*50 + "\n")

    def _run_render_test(self):
        """Тест производительности с отрисовкой"""
        import time
        
        print("\n" + "="*60)
        print("🎨 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ С ОТРИСОВКОЙ")
        print("="*60)
        
        # Сохраняем текущие объекты
        saved_enemies = self.enemies[:]
        saved_bases = self.enemy_bases[:]
        saved_asteroids = self.asteroids[:]
        
        test_results = []
        
        # ===== ТЕСТ 1: ВРАГИ =====
        print("\n📊 ТЕСТ 1: ВРАГИ (с отрисовкой)")
        enemy_counts = [10, 20, 50, 100, 200]
        
        for count in enemy_counts:
            self.enemies.clear()
            
            # Спавним врагов
            for i in range(count):
                x = self.ship.x + random.randint(-2000, 2000)
                y = self.ship.y + random.randint(-2000, 2000)
                enemy_type = random.choice(['scout', 'tank', 'sniper', 'kamikaze', 'swarmer'])
                enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type, self.difficulty_multiplier)
                if enemy:
                    self.enemies.append(enemy)
            
            # Замеряем FPS с отрисовкой
            fps_start = time.time()
            frame_count = 0
            target_frames = 120  # Больше кадров для точности
            
            for _ in range(target_frames):
                # ОБНОВЛЕНИЕ
                for enemy in self.enemies:
                    enemy.update(self.ship.x, self.ship.y)
                
                # ОТРИСОВКА (имитация)
                for enemy in self.enemies:
                    enemy.draw(self.screen, self.camera.x, self.camera.y, self.ship.x, self.ship.y)
                
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            
            print(f"  {count} врагов: {fps:.1f} FPS")
            test_results.append(("Враги", count, fps))
            
            self.enemies.clear()
        
        # ===== ТЕСТ 2: БАЗЫ =====
        print("\n📊 ТЕСТ 2: БАЗЫ (с отрисовкой)")
        base_counts = [5, 10, 20, 30, 50, 100, 150]
        
        for count in base_counts:
            self.enemy_bases.clear()
            
            # Спавним базы
            for i in range(count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
                base = EnemyBase(x, y, base_type)
                self.enemy_bases.append(base)
            
            # Замеряем FPS с отрисовкой
            fps_start = time.time()
            frame_count = 0
            target_frames = 120
            
            for _ in range(target_frames):
                # ОБНОВЛЕНИЕ
                for base in self.enemy_bases:
                    base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)
                
                # ОТРИСОВКА
                for base in self.enemy_bases:
                    base.draw(self.screen, self.camera.x, self.camera.y)
                
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            
            print(f"  {count} баз: {fps:.1f} FPS")
            test_results.append(("Базы", count, fps))
            
            self.enemy_bases.clear()
        
        # ===== ТЕСТ 3: АСТЕРОИДЫ =====
        print("\n📊 ТЕСТ 3: АСТЕРОИДЫ (с отрисовкой)")
        asteroid_counts = [10, 20, 50, 100, 200]
        
        for count in asteroid_counts:
            self.asteroids.clear()
            
            # Спавним астероиды
            for i in range(count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                asteroid = Asteroid(x, y)
                self.asteroids.append(asteroid)
            
            # Замеряем FPS с отрисовкой
            fps_start = time.time()
            frame_count = 0
            target_frames = 120
            
            for _ in range(target_frames):
                # ОБНОВЛЕНИЕ
                for asteroid in self.asteroids:
                    asteroid.update()
                
                # ОТРИСОВКА
                for asteroid in self.asteroids:
                    asteroid.draw(self.screen, self.camera.x, self.camera.y)
                
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            
            print(f"  {count} астероидов: {fps:.1f} FPS")
            test_results.append(("Астероиды", count, fps))
            
            self.asteroids.clear()
        
        # ===== ТЕСТ 4: СМЕШАННАЯ НАГРУЗКА =====
        print("\n📊 ТЕСТ 4: СМЕШАННАЯ НАГРУЗКА")
        scenarios = [
            ("10 врагов + 5 баз + 20 астероидов", 10, 5, 20),
            ("20 врагов + 10 баз + 50 астероидов", 20, 10, 50),
            ("50 врагов + 20 баз + 100 астероидов", 50, 20, 100),
            ("100 врагов + 30 баз + 200 астероидов", 100, 30, 200),
        ]
        
        for name, enemy_count, base_count, asteroid_count in scenarios:
            self.enemies.clear()
            self.enemy_bases.clear()
            self.asteroids.clear()
            
            # Спавним врагов
            for i in range(enemy_count):
                x = self.ship.x + random.randint(-2000, 2000)
                y = self.ship.y + random.randint(-2000, 2000)
                enemy_type = random.choice(['scout', 'tank', 'sniper', 'kamikaze', 'swarmer'])
                enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type, self.difficulty_multiplier)
                if enemy:
                    self.enemies.append(enemy)
            
            # Спавним базы
            for i in range(base_count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
                base = EnemyBase(x, y, base_type)
                self.enemy_bases.append(base)
            
            # Спавним астероиды
            for i in range(asteroid_count):
                x = self.ship.x + random.randint(-3000, 3000)
                y = self.ship.y + random.randint(-3000, 3000)
                asteroid = Asteroid(x, y)
                self.asteroids.append(asteroid)
            
            # Замеряем FPS
            fps_start = time.time()
            frame_count = 0
            target_frames = 120
            
            for _ in range(target_frames):
                # Обновление
                for enemy in self.enemies:
                    enemy.update(self.ship.x, self.ship.y)
                for base in self.enemy_bases:
                    base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)
                for asteroid in self.asteroids:
                    asteroid.update()
                
                # Отрисовка
                for enemy in self.enemies:
                    enemy.draw(self.screen, self.camera.x, self.camera.y, self.ship.x, self.ship.y)
                for base in self.enemy_bases:
                    base.draw(self.screen, self.camera.x, self.camera.y)
                for asteroid in self.asteroids:
                    asteroid.draw(self.screen, self.camera.x, self.camera.y)
                
                frame_count += 1
            
            fps_time = time.time() - fps_start
            fps = frame_count / fps_time if fps_time > 0 else 0
            
            print(f"  {name}: {fps:.1f} FPS")
            test_results.append(("Смешанная", 0, fps))
            
            self.enemies.clear()
            self.enemy_bases.clear()
            self.asteroids.clear()
        
        # ===== ИТОГ =====
        print("\n" + "="*60)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print("="*60)
        print(f"{'Тип':<15} {'Количество':<12} {'FPS':<10}")
        print("-"*40)
        for test_type, count, fps in test_results:
            print(f"{test_type:<15} {count:<12} {fps:.1f}")
        print("="*60 + "\n")
        
        # Восстанавливаем объекты
        self.enemies = saved_enemies
        self.enemy_bases = saved_bases
        self.asteroids = saved_asteroids

    def _run_real_test(self):
        """Тест с реальной нагрузкой (коллизии + все системы)"""
        import time
        
        print("\n" + "="*60)
        print("🎯 РЕАЛЬНЫЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*60)
        
        # Сохраняем текущие объекты
        saved_enemies = self.enemies[:]
        saved_bases = self.enemy_bases[:]
        saved_asteroids = self.asteroids[:]
        
        # Создаём тестовую сцену
        self.enemies.clear()
        self.enemy_bases.clear()
        self.asteroids.clear()
        
        # Спавним 150 баз
        print("\n📊 Создание 150 баз...")
        for i in range(150):
            x = self.ship.x + random.randint(-5000, 5000)
            y = self.ship.y + random.randint(-5000, 5000)
            base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
            base = EnemyBase(x, y, base_type)
            self.enemy_bases.append(base)
        
        # Спавним немного врагов
        print("📊 Создание 50 врагов...")
        for i in range(50):
            x = self.ship.x + random.randint(-2000, 2000)
            y = self.ship.y + random.randint(-2000, 2000)
            enemy_type = random.choice(['scout', 'tank', 'sniper', 'kamikaze', 'swarmer'])
            enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type, self.difficulty_multiplier)
            if enemy:
                self.enemies.append(enemy)
        
        print("📊 Запуск теста на 5 секунд...")
        
        # Замеряем реальный FPS
        fps_start = time.time()
        frame_count = 0
        test_duration = 60.0  # 5 секунд
        
        while time.time() - fps_start < test_duration:
            # ПОЛНОЕ ОБНОВЛЕНИЕ
            self._update_without_checks()
            
            # ПОЛНАЯ ОТРИСОВКА
            self._draw_without_flip()
            
            frame_count += 1
            
            # Ограничиваем чтобы не уйти в бесконечный цикл
            if frame_count > 100000:
                break
        
        fps_time = time.time() - fps_start
        real_fps = frame_count / fps_time if fps_time > 0 else 0
        
        print(f"\n📊 РЕЗУЛЬТАТ:")
        print(f"  ⏱️ Время: {fps_time:.2f} сек")
        print(f"  🎮 Кадров: {frame_count}")
        print(f"  🎮 Реальный FPS: {real_fps:.1f}")
        print(f"  🏠 Баз: {len(self.enemy_bases)}")
        print(f"  👾 Врагов: {len(self.enemies)}")
        
        # Восстанавливаем объекты
        self.enemies = saved_enemies
        self.enemy_bases = saved_bases
        self.asteroids = saved_asteroids
        
        print("="*60 + "\n")
    
    def _update_without_checks(self):
        """Обновление без проверок для теста"""
        # Обновляем врагов
        for enemy in self.enemies:
            enemy.update(self.ship.x, self.ship.y)
        
        # Обновляем базы
        for base in self.enemy_bases:
            base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)
        
        # Обновляем астероиды
        for asteroid in self.asteroids:
            asteroid.update()
        
        # Обновляем пули
        for bullet in self.bullets:
            bullet.update()
        
        # Обновляем частицы
        self.particles.update()
    
    def _draw_without_flip(self):
        """Отрисовка без flip для теста"""
        camera_x = self.camera.x
        camera_y = self.camera.y
        
        self.screen.fill(BLACK)
        
        # Рисуем все объекты
        for base in self.enemy_bases:
            base.draw(self.screen, camera_x, camera_y)
        
        for enemy in self.enemies:
            enemy.draw(self.screen, camera_x, camera_y, self.ship.x, self.ship.y)
        
        for asteroid in self.asteroids:
            asteroid.draw(self.screen, camera_x, camera_y)
        
        for bullet in self.bullets:
            bullet.draw(self.screen, camera_x, camera_y)
        
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen, camera_x, camera_y)
        
        self.particles.draw(self.screen, camera_x, camera_y)
        self.ship.draw(self.screen, camera_x, camera_y, self.particles)
        
    def is_near_base(self):
        """Проверяет, находится ли корабль рядом с базой"""
        dist = math.sqrt(
            (self.ship.x - self.player_base.x)**2 + 
            (self.ship.y - self.player_base.y)**2
        )
        return dist < 300
        
    # ============================================================
    #  ОТРИСОВКА
    # ============================================================

    def draw(self):
        """Отрисовка с зумом через камеру"""
        
        self.screen.fill(BLACK)
        
        # ===== 1. ОБНОВЛЯЕМ КАМЕРУ =====
        self.camera.update(self.ship.x, self.ship.y)
        
        # ===== 2. РИСУЕМ ВСЁ ЧЕРЕЗ КАМЕРУ =====
        
        self.starfield.draw(self.screen, self.camera)
        
        for asteroid in self.asteroids:
            asteroid.draw(self.screen, self.camera)
        
        self.particles.draw(self.screen, self.camera)
        self.powerups.draw(self.screen, self.camera)
        
        self.ship.draw(self.screen, self.camera, self.particles)
        
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen, self.camera)
        
        for base in self.enemy_bases:
            base.draw(self.screen, self.camera)
        
        self.player_base.draw(self.screen, self.camera)
        
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera, self.ship.x, self.ship.y)
        
        for outpost in self.outposts:
            outpost.draw(self.screen, self.camera)
        
        self.waypoint_manager.draw_in_game(self.screen, self.camera, self.ship.x, self.ship.y)
        self.indicators.draw(self.screen)
        
        # ===== 3. HUD =====
        self.minimap.draw(
            self.screen,
            self.ship.x, self.ship.y,
            self.enemies,
            self.powerups.powerups,
            self.player_base.x, self.player_base.y,
            self.camera,
            self.enemy_bases,
            self.outposts
        )
        
        self._draw_base_hp()
        self._draw_hud()
        
        if self.game_over:
            self._draw_game_over()
        
        self.world_map.draw(
            self.screen,
            self.ship.x, self.ship.y,
            self.enemies,
            self.enemy_bases,
            self.asteroids,
            self.chunk_manager,
            self.outposts
        )
        
        if self.hangar is not None and self.hangar.active:
            self.hangar.draw()
        
        # Варп
        if self.fuel_system.warp_active:
            vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(100, 0, -5):
                alpha = int(10 * (1 - i / 100))
                radius = i * 3
                pygame.draw.circle(vignette, (100, 200, 255, alpha), (WIDTH//2, HEIGHT//2), radius)
            self.screen.blit(vignette, (0, 0))
        
        pygame.display.flip()
        self.clock.tick(FPS)

    def _draw_base_hp(self):
        """Отображает HP базы под прицелом"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        camera_x, camera_y = self.camera.x, self.camera.y
        world_mouse_x = mouse_x + camera_x
        world_mouse_y = mouse_y + camera_y

        font = pygame.font.Font(None, 20)
        
        for base in self.enemy_bases:
            if not base.alive:
                continue

            dx = world_mouse_x - base.x
            dy = world_mouse_y - base.y
            dist = math.sqrt(dx**2 + dy**2)

            if dist < base.radius + 30:
                # Фон для текста
                hp_text = font.render(f"BASE HP: {int(base.health)}/{int(base.max_health)}", True, (255, 255, 255))
                hp_rect = hp_text.get_rect(center=(mouse_x, mouse_y - 50))
                
                # Тень
                shadow_rect = hp_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                shadow = font.render(f"BASE HP: {int(base.health)}/{int(base.max_health)}", True, (0, 0, 0))
                self.screen.blit(shadow, shadow_rect)
                
                # Основной текст
                self.screen.blit(hp_text, hp_rect)
                break
                
    def _draw_hud(self):
        """Рисует интерфейс"""
        
        hud_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        # ===== ЛЕВЫЙ ВЕРХНИЙ УГОЛ =====
        score_text = hud_font.render(f"SCORE: {self.score}", True, (255, 255, 100))
        self.screen.blit(score_text, (15, 15))
        
        hp_color = (50, 255, 50) if self.ship.health > 30 else (255, 50, 50)
        hp_text = hud_font.render(f"HP: {self.ship.health}", True, hp_color)
        self.screen.blit(hp_text, (15, 40))
        
        # Топливо (под HP)
        self.fuel_system.draw_hud(self.screen)
        
        # ===== РЕСУРСЫ =====
        resource_y = 115
        resource_colors = {
            'scrap': (150, 150, 150),
            'crystal': (100, 200, 255),
            'fuel': (255, 200, 50),
        }
        resource_icons = {
            'scrap': '[S]',
            'crystal': '[C]',
            'fuel': '[F]',
        }
        
        for res_type, amount in self.resources.items():
            if amount > 0:
                color = resource_colors.get(res_type, (200, 200, 200))
                icon = resource_icons.get(res_type, '')
                text = small_font.render(f"{icon} {amount}", True, color)
                self.screen.blit(text, (15, resource_y))
                resource_y += 20
        
        # ===== ПРАВЫЙ ВЕРХНИЙ УГОЛ =====
        minimap_width = 150
        right_x = WIDTH - minimap_width - 30
        
        enemy_text = hud_font.render(f"ENEMIES: {len(self.enemies)}", True, (255, 100, 100))
        enemy_rect = enemy_text.get_rect(topright=(right_x, 15))
        self.screen.blit(enemy_text, enemy_rect)
        
        bases_alive = sum(1 for b in self.enemy_bases if b.alive)
        bases_text = hud_font.render(f"BASES: {bases_alive}", True, (255, 200, 100))
        bases_rect = bases_text.get_rect(topright=(right_x, 40))
        self.screen.blit(bases_text, bases_rect)
        
        outposts_alive = sum(1 for o in self.outposts if o.alive)
        outposts_text = hud_font.render(f"OUTPOSTS: {outposts_alive}", True, (100, 200, 255))
        outposts_rect = outposts_text.get_rect(topright=(right_x, 65))
        self.screen.blit(outposts_text, outposts_rect)
        
        if self.config.get('game.show_fps', False):
            fps_text = small_font.render(f"FPS: {int(self.clock.get_fps())}", True, (100, 100, 100))
            fps_rect = fps_text.get_rect(topright=(right_x, 90))
            self.screen.blit(fps_text, fps_rect)
        
        if self.config.get('game.debug_mode', False):
            debug_text = small_font.render("DEBUG", True, (255, 200, 50))
            debug_rect = debug_text.get_rect(topright=(right_x, 115))
            self.screen.blit(debug_text, debug_rect)
        
        # ===== ПРЕДУПРЕЖДЕНИЕ О ТОПЛИВЕ =====
        if self.fuel_system.fuel <= 0:
            warning_text = hud_font.render("NO FUEL!", True, (255, 50, 50))
            warning_rect = warning_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(warning_text, warning_rect)
        elif self.fuel_system.fuel < 20:
            warning_text = small_font.render("LOW FUEL", True, (255, 200, 50))
            warning_rect = warning_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(warning_text, warning_rect)
        
        # ===== ЛЕВЫЙ НИЖНИЙ УГОЛ =====
        speed_val = math.sqrt(self.ship.speed_x**2 + self.ship.speed_y**2)
        speed_text = small_font.render(f"SPEED: {speed_val:.1f}", True, (150, 150, 150))
        self.screen.blit(speed_text, (15, HEIGHT - 30))
        
        # ===== ПРАВЫЙ НИЖНИЙ УГОЛ =====
        controls_text = small_font.render("ESC: Menu | P: Pause", True, (100, 100, 100))
        controls_rect = controls_text.get_rect(bottomright=(WIDTH - 15, HEIGHT - 15))
        self.screen.blit(controls_text, controls_rect)
        
        # ===== ЦЕНТР ВВЕРХУ =====
        if self.paused:
            pause_text = hud_font.render("PAUSED", True, (255, 255, 255))
            pause_rect = pause_text.get_rect(center=(WIDTH // 2, 30))
            self.screen.blit(pause_text, pause_rect)
        
        # ===== АКТИВНЫЕ ЭФФЕКТЫ =====
        effects_colors = {
            'shield': (50, 150, 255),
            'triple_shot': (255, 200, 50),
            'speed_boost': (50, 255, 150),
            'bomb': (255, 100, 200),
            'magnet': (200, 100, 255),
        }
        
        y_offset = 115 + len(self.resources) * 20 + 10
        for effect, timer in self.powerups.active_effects.items():
            if timer > 0:
                seconds = timer // 60
                color = effects_colors.get(effect, (255, 255, 255))
                effect_text = small_font.render(f"{effect.upper()}: {seconds}s", True, color)
                self.screen.blit(effect_text, (15, y_offset))
                y_offset += 20
        
        # ===== DEBUG MODE =====
        if self.config.get('game.debug_mode', False):
            cheats_text = small_font.render(
                "F1:Bomb  F2:Heal  F3:+50  F4:Kill  F5:Spawn  F6:Load  F7:Clean  F8:Test  F9:Render  F10:Real",
                True, (80, 80, 80)
            )
            cheats_rect = cheats_text.get_rect(center=(WIDTH // 2, HEIGHT - 15))
            self.screen.blit(cheats_text, cheats_rect)
            
            pos_text = small_font.render(f"POS: ({int(self.ship.x)}, {int(self.ship.y)})", True, (80, 80, 80))
            pos_rect = pos_text.get_rect(bottomleft=(15, HEIGHT - 55))
            self.screen.blit(pos_text, pos_rect)
        
        # ===== ПОДСКАЗКА ПО КАРТЕ =====
        map_hint = small_font.render("TAB: World Map | RMB: Set Waypoint", True, (80, 80, 100))
        map_rect = map_hint.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        self.screen.blit(map_hint, map_rect)
        
        # ===== ВЗАИМОДЕЙСТВИЕ С АВАНПОСТОМ =====
        near_outpost = False
        for outpost in self.outposts:
            if not outpost.alive:
                continue
            dist = math.sqrt((outpost.x - self.ship.x)**2 + (outpost.y - self.ship.y)**2)
            if dist < 200:
                near_outpost = True
                break
        
        if near_outpost:
            interact_text = small_font.render("Press E to interact", True, (255, 255, 100))
            interact_rect = interact_text.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            self.screen.blit(interact_text, interact_rect)
        
        # ===== СООБЩЕНИЕ ОБ АНГАРЕ =====
        if self.hangar_not_available:
            msg_text = small_font.render("Ангар доступен только на базе!", True, (255, 100, 100))
            msg_rect = msg_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            # Мерцание
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(msg_text, msg_rect)
        
        # ===== ПОДСКАЗКА АНГАРА (только на базе) =====
        if self.is_near_base():
            hangar_hint = small_font.render("[H] Открыть ангар", True, (100, 200, 255))
            hangar_rect = hangar_hint.get_rect(center=(WIDTH // 2, HEIGHT - 70))
            self.screen.blit(hangar_hint, hangar_rect)   
            
    def _draw_game_over(self):
        """Экран Game Over — чистый и понятный"""
        # Затемнение
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Шрифты
        title_font = pygame.font.Font(None, 72)
        big_font = pygame.font.Font(None, 48)
        medium_font = pygame.font.Font(None, 32)
        
        # Заголовок
        title = title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        self.screen.blit(title, title_rect)
        
        # Счёт
        score_text = big_font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 10))
        self.screen.blit(score_text, score_rect)
        
        # Подсказки
        restart_text = medium_font.render("Press SPACE to restart", True, (255, 255, 100))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = medium_font.render("Press ESC for menu", True, (150, 150, 150))
        menu_rect = menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 95))
        self.screen.blit(menu_text, menu_rect)
        
    # ============================================================
    #  ЗАПУСК
    # ============================================================

    def run(self):
        """Запускает игровой цикл"""
        while self.running:
            result = self.handle_events()
            if result == "menu":
                return "menu"
            elif result == "quit":
                return "quit"

            self.update()
            self.draw()

        return "quit"
        

