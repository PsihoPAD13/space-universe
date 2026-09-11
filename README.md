# 🚀 Space Universe

> **Космический шутер с бесконечным миром, базами-ульями и процедурной генерацией.**

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green)](https://www.pygame.org/)
[![Version](https://img.shields.io/badge/Version-0.12.0-blue)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 О игре

**Space Universe** — это бесконечный космический шутер с элементами выживания и стратегии. Исследуй процедурно-генерируемый мир, сражайся с врагами, уничтожай базы-ульи, собирай ресурсы и улучшай корабль.

### 🎯 Особенности

- 🌌 **Бесконечный мир** — процедурная генерация чанков с сохранением на диск
- 🛸 **Инерционная физика** — реалистичное управление кораблём
- 👾 **7 типов врагов** — разные стратегии и поведение
- 🐝 **Базы-ульи** — враги вылетают при приближении и возвращаются при отлёте
- 💎 **6 типов бонусов** — здоровье, щит, тройной выстрел, ускорение, бомба, магнит
- ⛽ **Топливо и варп** — ускорение x5 с расходом топлива
- 🏠 **База игрока** — восстановление HP
- 🪨 **Астероиды** — добыча ресурсов
- 🗺️ **Большая карта мира** — зум, перетаскивание, маркеры
- 🎨 **Чистый интерфейс** — вся информация на виду
- 💾 **Автосохранение** — прогресс сохраняется между сессиями

---

## 🖥️ Управление

| Клавиша | Действие |
|---------|----------|
| `W` / `↑` | Газ (ускорение) |
| `A` / `←` | Поворот налево |
| `D` / `→` | Поворот направо |
| `Space` / `ЛКМ` | Стрельба |
| `Shift` | Варп (ускорение x5) |
| `P` | Пауза |
| `ESC` | Меню / Выход |
| `TAB` | Большая карта мира |
| `ПКМ` на карте | Установить маркер |
| `C` | Удалить маркер |
| `R` на карте | Сброс вида |

### 🐞 Режим отладки (Debug Mode)

Включи в настройках для доступа к читам:

| Клавиша | Действие |
|---------|----------|
| `F1` | Бомба (уничтожить всех врагов) |
| `F2` | Восстановить HP |
| `F3` | +50 очков |
| `F4` | Убить всех врагов |
| `F5` | Спавн 5 врагов |
| `F6` | Принудительная загрузка баз из файлов |
| `F7` | Очистка файлов от мёртвых баз |

---

## 📦 Установка и запуск

### 1. Клонируй репозиторий
```bash
git clone https://github.com/PsihoPAD13/space-shooter.git
cd space-shooter
```

### 2. Установи зависимости
```
bash
pip install pygame
```

### 3. Запусти игру
```
bash
python main.py
```

---

## 🧩 Структура проекта
```
space_universe/
├── core/              # Игровой цикл, камера
│   ├── game.py
│   └── camera.py
├── entities/          # Игровые объекты
│   ├── ship.py
│   ├── enemy.py
│   ├── enemy_types.py
│   ├── enemy_manager.py
│   ├── base.py
│   ├── bullet.py
│   ├── powerups.py
│   └── asteroid.py
├── systems/           # Игровые системы
│   ├── particles.py
│   ├── minimap.py
│   ├── direction_indicators.py
│   ├── fuel.py
│   ├── world_map.py
│   └── waypoints.py
├── world/             # Мир и чанки
│   ├── chunk.py
│   ├── chunk_manager.py
│   └── starfield_background.py
├── ui/                # Интерфейс
│   ├── menu.py
│   └── settings_menu.py
├── world_data/        # Сохранения (создаётся автоматически)
├── main.py
├── settings.py
├── config_manager.py
├── utils.py
├── version.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## 🎮 Скриншоты

<img width="450" height="350" alt="image" src="https://github.com/user-attachments/assets/aeec193f-d6a6-4c8a-a833-197287cecc1b" />
<img width="450" height="350" alt="image" src="https://github.com/user-attachments/assets/7050e824-53ce-42a5-8b07-1051c5e63fe4" />
<img width="450" height="350" alt="image" src="https://github.com/user-attachments/assets/06f94101-7594-4ddf-9051-cdd4dd9b64ee" />
<img width="450" height="350" alt="image" src="https://github.com/user-attachments/assets/d4c93e56-7cba-43cc-96a6-11fe67aa51c4" />

---

## 📜 Лицензия

MIT License — свободно используй, модифицируй и распространяй.

---

## 🙏 Благодарности

Pygame — за отличный игровой фреймворк

Всем, кто тестировал и давал обратную связь ❤️
