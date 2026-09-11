# core/camera.py

class Camera:
    def __init__(self, x, y, width, height, zoom=1.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.zoom = zoom
        self.target_zoom = zoom
        self.zoom_speed = 0.15
        self.min_zoom = 0.3
        self.max_zoom = 3.0
    
    def update(self, target_x, target_y):
        """Центрирует камеру на цели"""
        # Видимая область в мировых координатах
        view_w = self.width / self.zoom
        view_h = self.height / self.zoom
        
        self.x = target_x - view_w / 2
        self.y = target_y - view_h / 2
        
        # Плавный зум
        self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed
    
    def world_to_screen(self, wx, wy):
        """Мировые → экранные координаты"""
        return (
            (wx - self.x) * self.zoom,
            (wy - self.y) * self.zoom
        )
    
    def screen_to_world(self, sx, sy):
        """Экранные → мировые координаты"""
        return (
            sx / self.zoom + self.x,
            sy / self.zoom + self.y
        )
    
    def zoom_in(self):
        self.target_zoom = min(self.max_zoom, self.target_zoom + 0.1)
    
    def zoom_out(self):
        self.target_zoom = max(self.min_zoom, self.target_zoom - 0.1)
    
    def get_view_rect(self):
        """Возвращает видимую область в мировых координатах"""
        view_w = self.width / self.zoom
        view_h = self.height / self.zoom
        return (self.x, self.y, view_w, view_h)