import pygame
import math
import sys
import time

pygame.init()
width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Симуляция радиоволн, сонара и радара")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)


class Button:
    def __init__(self, rect, text, action, active=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.active = active
        self.hovered = False

    def draw(self, screen):
        if self.active:
            color = (100, 150, 100)
            border_color = (150, 255, 150)
        elif self.hovered:
            color = (80, 80, 120)
            border_color = (120, 120, 180)
        else:
            color = (70, 70, 70)
            border_color = (120, 120, 120)

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)

        text_surface = small_font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return self.action
        return None


class Slider:
    def __init__(self, rect, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        self.slider_pos = self.value_to_pos(initial_val)

    def value_to_pos(self, value):
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + ratio * self.rect.width

    def pos_to_value(self, pos):
        ratio = (pos - self.rect.x) / self.rect.width
        ratio = max(0, min(1, ratio))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                slider_rect = pygame.Rect(self.slider_pos - 5, self.rect.y - 5, 10, self.rect.height + 10)
                if slider_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                    self.dragging = True
                    self.slider_pos = max(self.rect.x, min(self.rect.x + self.rect.width, mouse_x))
                    self.val = self.pos_to_value(self.slider_pos)
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                self.slider_pos = max(self.rect.x, min(self.rect.x + self.rect.width, mouse_x))
                self.val = self.pos_to_value(self.slider_pos)
                return True
        return False

    def draw(self, screen):
        pygame.draw.line(screen, (120, 120, 120),
                         (self.rect.x, self.rect.centery),
                         (self.rect.x + self.rect.width, self.rect.centery), 3)

        pygame.draw.circle(screen, (200, 200, 200),
                           (int(self.slider_pos), self.rect.centery), 8)
        pygame.draw.circle(screen, (255, 255, 255),
                           (int(self.slider_pos), self.rect.centery), 8, 2)

        label_text = small_font.render(f"{self.label}: {self.val:.1f}", True, (200, 200, 200))
        screen.blit(label_text, (self.rect.x, self.rect.y - 20))


class RadioWave:
    def __init__(self, origin, frequency=1.0, speed=2):
        self.origin = origin
        self.radius = 0
        self.frequency = frequency
        self.speed = speed
        self.active = True
        self.max_radius = 600

    def update(self):
        if self.active:
            self.radius += self.speed
            if self.radius > self.max_radius:
                self.active = False

    def draw(self, screen):
        if self.active:
            ring_spacing = 50 / self.frequency
            for i in range(int(self.radius / ring_spacing) + 1):
                ring_radius = i * ring_spacing
                if ring_radius <= self.radius and ring_radius > 0:
                    alpha = max(0, 255 - int(ring_radius * 0.5))
                    color = (0, min(255, alpha), min(255, alpha))
                    if ring_radius < width and ring_radius < height:
                        pygame.draw.circle(screen, color, self.origin, int(ring_radius), 2)


class SonarPulse:
    def __init__(self, origin, frequency=0.5, speed=1.5):
        self.origin = origin
        self.radius = 0
        self.frequency = frequency
        self.speed = speed
        self.active = True
        self.max_radius = 400
        self.detections = []

    def update(self, obstacles):
        if self.active:
            self.radius += self.speed
            if self.radius > self.max_radius:
                self.active = False

            # Проверяем обнаружение объектов
            for obstacle in obstacles:
                for point in obstacle.points:
                    dist = math.sqrt((point[0] - self.origin[0]) ** 2 + (point[1] - self.origin[1]) ** 2)
                    if abs(dist - self.radius) < 5:  # Обнаружение при касании
                        detection = {
                            'point': point,
                            'distance': dist,
                            'angle': math.atan2(point[1] - self.origin[1], point[0] - self.origin[0]),
                            'obstacle': obstacle
                        }
                        if detection not in self.detections:
                            self.detections.append(detection)

    def draw(self, screen):
        if self.active:
            # Основная волна сонара (синие концентрические круги)
            ring_spacing = 80 / self.frequency
            for i in range(int(self.radius / ring_spacing) + 1):
                ring_radius = i * ring_spacing
                if ring_radius <= self.radius and ring_radius > 0:
                    alpha = max(0, 200 - int(ring_radius * 0.8))
                    color = (0, 0, min(255, alpha))
                    if ring_radius < width and ring_radius < height:
                        pygame.draw.circle(screen, color, self.origin, int(ring_radius), 3)


class RadarSweep:
    def __init__(self, origin, range_radius=300, sweep_speed=2):
        self.origin = origin
        self.range_radius = range_radius
        self.sweep_angle = 0
        self.sweep_speed = sweep_speed
        self.active = True
        self.detections = []
        self.sweep_width = math.pi / 6  # 30 градусов ширина луча

    def update(self, obstacles):
        if self.active:
            self.sweep_angle += self.sweep_speed * math.pi / 180  # Конвертируем в радианы
            if self.sweep_angle >= 2 * math.pi:
                self.sweep_angle = 0
                self.detections.clear()  # Очищаем старые обнаружения при новом обороте

            # Проверяем обнаружение объектов в текущем секторе
            for obstacle in obstacles:
                center_x = sum(p[0] for p in obstacle.points) / len(obstacle.points)
                center_y = sum(p[1] for p in obstacle.points) / len(obstacle.points)

                dist = math.sqrt((center_x - self.origin[0]) ** 2 + (center_y - self.origin[1]) ** 2)
                if dist <= self.range_radius:
                    obj_angle = math.atan2(center_y - self.origin[1], center_x - self.origin[0])
                    if obj_angle < 0:
                        obj_angle += 2 * math.pi

                    # Проверяем, попадает ли объект в луч радара
                    angle_diff = abs(obj_angle - self.sweep_angle)
                    if angle_diff > math.pi:
                        angle_diff = 2 * math.pi - angle_diff

                    if angle_diff <= self.sweep_width / 2:
                        detection = {
                            'point': (center_x, center_y),
                            'distance': dist,
                            'angle': obj_angle,
                            'obstacle': obstacle
                        }
                        # Добавляем только уникальные обнаружения
                        if not any(d['obstacle'] == obstacle for d in self.detections):
                            self.detections.append(detection)

    def draw(self, screen):
        if self.active:
            # Рисуем окружность дальности радара
            pygame.draw.circle(screen, (100, 100, 0), self.origin, self.range_radius, 1)

            # Рисуем луч радара
            beam_end_x = self.origin[0] + self.range_radius * math.cos(self.sweep_angle)
            beam_end_y = self.origin[1] + self.range_radius * math.sin(self.sweep_angle)

            # Основной луч
            pygame.draw.line(screen, (255, 255, 0), self.origin, (beam_end_x, beam_end_y), 3)

            # Конус луча
            left_angle = self.sweep_angle - self.sweep_width / 2
            right_angle = self.sweep_angle + self.sweep_width / 2

            left_x = self.origin[0] + self.range_radius * math.cos(left_angle)
            left_y = self.origin[1] + self.range_radius * math.sin(left_angle)
            right_x = self.origin[0] + self.range_radius * math.cos(right_angle)
            right_y = self.origin[1] + self.range_radius * math.sin(right_angle)

            pygame.draw.line(screen, (200, 200, 0), self.origin, (left_x, left_y), 1)
            pygame.draw.line(screen, (200, 200, 0), self.origin, (right_x, right_y), 1)

            # Рисуем обнаруженные объекты на радаре
            for detection in self.detections:
                point = detection['point']
                # Мигающий маркер для обнаруженных объектов
                if int(time.time() * 4) % 2:  # Мигание 2 раза в секунду
                    pygame.draw.circle(screen, (255, 0, 0), (int(point[0]), int(point[1])), 8, 3)


class ReflectedWave:
    def __init__(self, origin, direction, frequency=1.0, speed=2, intensity=1.0):
        self.origin = origin
        self.direction = direction
        self.radius = 0
        self.frequency = frequency
        self.speed = speed
        self.intensity = intensity
        self.active = True
        self.max_radius = 400

    def update(self):
        if self.active:
            self.radius += self.speed
            if self.radius > self.max_radius:
                self.active = False

    def draw(self, screen):
        if self.active:
            ring_spacing = 50 / self.frequency
            for i in range(int(self.radius / ring_spacing) + 1):
                ring_radius = i * ring_spacing
                if ring_radius <= self.radius and ring_radius > 0:
                    alpha = max(0, int(200 * self.intensity - ring_radius * 0.7))
                    color = (0, min(255, alpha), 0)
                    if ring_radius < width and ring_radius < height:
                        pygame.draw.circle(screen, color, self.origin, int(ring_radius), 1)


class TransmittedWave:
    def __init__(self, origin, direction, frequency=1.0, speed=2, intensity=1.0):
        self.origin = origin
        self.direction = direction
        self.radius = 0
        self.frequency = frequency
        self.speed = speed
        self.intensity = intensity
        self.active = True
        self.max_radius = 400

    def update(self):
        if self.active:
            self.radius += self.speed
            if self.radius > self.max_radius:
                self.active = False

    def draw(self, screen):
        if self.active:
            ring_spacing = 50 / self.frequency
            for i in range(int(self.radius / ring_spacing) + 1):
                ring_radius = i * ring_spacing
                if ring_radius <= self.radius and ring_radius > 0:
                    alpha = max(0, int(150 * self.intensity - ring_radius * 0.5))
                    color = (min(255, alpha), 0, min(255, alpha))
                    if ring_radius < width and ring_radius < height:
                        pygame.draw.circle(screen, color, self.origin, int(ring_radius), 1)


class Material:
    def __init__(self, name, absorption, reflection, transmission, color):
        self.name = name
        self.absorption = absorption
        self.reflection = reflection
        self.transmission = transmission
        self.color = color


# Определяем материалы
MATERIALS = {
    "RAM": Material("RAM", 0.95, 0.05, 0.0, (20, 20, 20)),
    "BRICK": Material("Кирпич", 0.7, 0.3, 0.0, (139, 69, 19)),
    "PAPER": Material("Бумага", 0.1, 0.1, 0.8, (255, 248, 220)),
    "GLASS": Material("Стекло", 0.05, 0.15, 0.8, (173, 216, 230)),
    "MIRROR": Material("Зеркало", 0.02, 0.98, 0.0, (192, 192, 192)),
    "WATER": Material("Вода", 0.3, 0.1, 0.6, (64, 164, 223)),
    "METAL": Material("Металл", 0.1, 0.9, 0.0, (169, 169, 169))
}


class Obstacle:
    def __init__(self, points, material_key="BRICK"):
        self.points = points
        self.rect = self.get_bounding_rect()
        self.material = MATERIALS[material_key]

    def get_bounding_rect(self):
        if not self.points:
            return pygame.Rect(0, 0, 0, 0)
        min_x = min(p[0] for p in self.points)
        max_x = max(p[0] for p in self.points)
        min_y = min(p[1] for p in self.points)
        max_y = max(p[1] for p in self.points)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def draw(self, screen):
        if len(self.points) > 2:
            pygame.draw.polygon(screen, self.material.color, self.points)
            border_color = tuple(min(255, c + 50) for c in self.material.color)
            pygame.draw.polygon(screen, border_color, self.points, 2)

            center_x = sum(p[0] for p in self.points) // len(self.points)
            center_y = sum(p[1] for p in self.points) // len(self.points)

            material_text = small_font.render(self.material.name, True, (255, 255, 255))
            text_rect = material_text.get_rect(center=(center_x, center_y))

            bg_rect = text_rect.inflate(8, 4)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(180)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, bg_rect)
            screen.blit(material_text, text_rect)


def calculate_reflection(wave_center, collision_point, obstacle):
    min_dist = float('inf')
    best_normal = (0, 1)

    for i in range(len(obstacle.points)):
        p1 = obstacle.points[i]
        p2 = obstacle.points[(i + 1) % len(obstacle.points)]

        line_vec = (p2[0] - p1[0], p2[1] - p1[1])
        line_len = math.sqrt(line_vec[0] ** 2 + line_vec[1] ** 2)

        if line_len > 0:
            line_unit = (line_vec[0] / line_len, line_vec[1] / line_len)
            normal = (-line_unit[1], line_unit[0])

            to_point = (collision_point[0] - p1[0], collision_point[1] - p1[1])
            dist = abs(to_point[0] * normal[0] + to_point[1] * normal[1])

            if dist < min_dist:
                min_dist = dist
                best_normal = normal

    incident = (collision_point[0] - wave_center[0], collision_point[1] - wave_center[1])
    incident_len = math.sqrt(incident[0] ** 2 + incident[1] ** 2)

    if incident_len > 0:
        incident_unit = (incident[0] / incident_len, incident[1] / incident_len)
        dot_product = incident_unit[0] * best_normal[0] + incident_unit[1] * best_normal[1]
        reflection = (
            incident_unit[0] - 2 * dot_product * best_normal[0],
            incident_unit[1] - 2 * dot_product * best_normal[1]
        )
        return reflection

    return (1, 0)


def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def check_wave_collision(wave, obstacles):
    collisions = []

    for obstacle in obstacles:
        center_x, center_y = wave.origin
        num_checks = 36
        for i in range(num_checks):
            angle = 2 * math.pi * i / num_checks
            check_x = center_x + wave.radius * math.cos(angle)
            check_y = center_y + wave.radius * math.sin(angle)

            if point_in_polygon((check_x, check_y), obstacle.points):
                collision_point = (check_x, check_y)
                reflection_dir = calculate_reflection(wave.origin, collision_point, obstacle)
                collisions.append({
                    "obstacle": obstacle,
                    "point": collision_point,
                    "direction": reflection_dir,
                    "material": obstacle.material
                })
                break

    return collisions


# Переменные состояния
wave_source = (width // 4, height // 2)
sonar_source = (width // 4, height // 4)
radar_source = (width // 4, 3 * height // 4)
frequency = 1.0
wave_speed = 2
waves = []
sonar_pulses = []
radar_sweeps = []
reflected_waves = []
transmitted_waves = []
obstacles = []
current_obstacle_points = []
current_material = "BRICK"
mode = "SOURCE"
system_type = "RADIO"
drawing = False

# UI элементы
ui_rect = pygame.Rect(width - 380, 0, 380, height)

# Создаем кнопки режимов
mode_buttons = [
    Button((width - 370, 50, 110, 25), "Источник", "SOURCE"),
    Button((width - 250, 50, 110, 25), "Рисовать", "DRAW"),
    Button((width - 130, 50, 110, 25), "Очистить", "CLEAR"),
]

# Кнопки типов систем
system_buttons = [
    Button((width - 370, 90, 110, 25), "Радиоволны", "RADIO"),
    Button((width - 250, 90, 110, 25), "Сонар", "SONAR"),
    Button((width - 130, 90, 110, 25), "Радар", "RADAR"),
]

# Кнопки действий
action_buttons = [
    Button((width - 370, 130, 110, 25), "Импульс", "PULSE"),
    Button((width - 250, 130, 110, 25), "Авто режим", "AUTO"),
    Button((width - 130, 130, 110, 25), "Стоп", "STOP"),
]

# Кнопки материалов (уменьшенные для экономии места)
material_buttons = []
materials_list = list(MATERIALS.keys())
for i, (key, material) in enumerate(MATERIALS.items()):
    x = width - 370 + (i % 3) * 120
    y = 300 + (i // 3) * 30
    material_buttons.append(Button((x, y, 110, 25), material.name, key))

# Слайдеры
frequency_slider = Slider((width - 350, 200, 180, 20), 0.1, 5.0, frequency, "Частота")
speed_slider = Slider((width - 350, 240, 180, 20), 1, 10, wave_speed, "Скорость")

# Автоматический режим
auto_mode = False
auto_timer = 0
auto_interval = 120  # кадры между импульсами

# Устанавливаем активные кнопки
for button in mode_buttons:
    if button.action == mode:
        button.active = True

for button in system_buttons:
    if button.action == system_type:
        button.active = True

for button in material_buttons:
    if button.action == current_material:
        button.active = True


def draw_ui(screen):
    # Фон UI
    pygame.draw.rect(screen, (40, 40, 40), ui_rect)
    pygame.draw.line(screen, (100, 100, 100), (width - 380, 0), (width - 380, height), 2)

    # Заголовок
    title = font.render("Панель управления", True, (255, 255, 255))
    screen.blit(title, (width - 370, 10))

    # Текущий режим и система
    mode_text = small_font.render(f"Режим: {mode} | Система: {system_type}", True, (200, 255, 200))
    screen.blit(mode_text, (width - 370, 170))

    # Кнопки
    for button in mode_buttons + system_buttons + action_buttons:
        button.draw(screen)

    # Слайдеры
    frequency_slider.draw(screen)
    speed_slider.draw(screen)

    # Заголовок материалов
    materials_title = font.render("Материалы:", True, (255, 255, 150))
    screen.blit(materials_title, (width - 370, 275))

    # Кнопки материалов
    for button in material_buttons:
        button.draw(screen)

    # Информация о текущем материале
    y_offset = 450
    if current_material in MATERIALS:
        material = MATERIALS[current_material]
        current_mat_text = small_font.render(f"Текущий: {material.name}", True, (255, 255, 150))
        screen.blit(current_mat_text, (width - 370, y_offset))
        y_offset += 20

        properties = [
            f"Поглощение: {material.absorption * 100:.0f}%",
            f"Отражение: {material.reflection * 100:.0f}%",
            f"Прохождение: {material.transmission * 100:.0f}%"
        ]

        for prop in properties:
            prop_text = small_font.render(prop, True, (200, 200, 255))
            screen.blit(prop_text, (width - 370, y_offset))
            y_offset += 15

    # Позиции источников
    y_offset += 20
    sources_title = font.render("Источники:", True, (255, 255, 150))
    screen.blit(sources_title, (width - 370, y_offset))
    y_offset += 20

    sources_info = [
        f"Радио: ({wave_source[0]}, {wave_source[1]})",
        f"Сонар: ({sonar_source[0]}, {sonar_source[1]})",
        f"Радар: ({radar_source[0]}, {radar_source[1]})"
    ]

    for info in sources_info:
        info_text = small_font.render(info, True, (180, 180, 180))
        screen.blit(info_text, (width - 370, y_offset))
        y_offset += 15

    # Статистика
    y_offset += 15
    stats = [
        f"Препятствий: {len(obstacles)}",
        f"Радиоволн: {len(waves)}",
        f"Сонар импульсы: {len(sonar_pulses)}",
        f"Радар активен: {'Да' if radar_sweeps else 'Нет'}",
        f"Авто режим: {'Вкл' if auto_mode else 'Выкл'}"
    ]

    stats_title = font.render("Статистика:", True, (255, 255, 150))
    screen.blit(stats_title, (width - 370, y_offset))
    y_offset += 20

    for stat in stats:
        stat_text = small_font.render(stat, True, (180, 180, 180))
        screen.blit(stat_text, (width - 370, y_offset))
        y_offset += 15

    # Обнаружения радара
    if radar_sweeps:
        radar = radar_sweeps[0]
        if radar.detections:
            y_offset += 10
            detect_title = small_font.render("Обнаружения радара:", True, (255, 255, 0))
            screen.blit(detect_title, (width - 370, y_offset))
            y_offset += 15

            for i, detection in enumerate(radar.detections[-3:]):  # Показываем последние 3
                dist = detection['distance']
                angle_deg = detection['angle'] * 180 / math.pi
                detect_text = small_font.render(f"{i + 1}. Дист: {dist:.0f}, Угол: {angle_deg:.0f}°", True,
                                                (255, 255, 0))
                screen.blit(detect_text, (width - 370, y_offset))
                y_offset += 15

    # Легенда цветов
    y_offset += 10
    colors_title = font.render("Легенда:", True, (255, 255, 150))
    screen.blit(colors_title, (width - 370, y_offset))
    y_offset += 20

    legend = [
        ("Радиоволны", (0, 200, 200)),
        ("Сонар", (0, 0, 200)),
        ("Радар", (255, 255, 0)),
        ("Отражённые", (0, 200, 0)),
        ("Прошедшие", (200, 0, 200))
    ]

    for name, color in legend:
        pygame.draw.circle(screen, color, (width - 360, y_offset + 8), 5)
        legend_text = small_font.render(name, True, (200, 200, 200))
        screen.blit(legend_text, (width - 340, y_offset))
        y_offset += 16


# Основной цикл
running = True
while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Обработка слайдеров
        if frequency_slider.handle_event(event):
            frequency = frequency_slider.val
        if speed_slider.handle_event(event):
            wave_speed = int(speed_slider.val)

        # Обработка кнопок режимов
        for button in mode_buttons:
            action = button.handle_event(event)
            if action:
                if action in ["SOURCE", "DRAW"]:
                    for b in mode_buttons:
                        b.active = (b.action == action)
                    mode = action
                elif action == "CLEAR":
                    waves.clear()
                    sonar_pulses.clear()
                    radar_sweeps.clear()
                    reflected_waves.clear()
                    transmitted_waves.clear()
                    obstacles.clear()
                    current_obstacle_points.clear()

        # Обработка кнопок типов систем
        for button in system_buttons:
            action = button.handle_event(event)
            if action and action in ["RADIO", "SONAR", "RADAR"]:
                for b in system_buttons:
                    b.active = (b.action == action)
                system_type = action

        # Обработка кнопок действий
        for button in action_buttons:
            action = button.handle_event(event)
            if action:
                if action == "PULSE":
                    if system_type == "RADIO":
                        waves.append(RadioWave(wave_source, frequency, wave_speed))
                    elif system_type == "SONAR":
                        sonar_pulses.append(SonarPulse(sonar_source, frequency * 0.5, wave_speed * 0.8))
                    elif system_type == "RADAR":
                        if not radar_sweeps:  # Добавляем радар только если его нет
                            radar_sweeps.append(RadarSweep(radar_source, 250, 3))
                elif action == "AUTO":
                    auto_mode = not auto_mode
                    for b in action_buttons:
                        if b.action == "AUTO":
                            b.active = auto_mode
                elif action == "STOP":
                    auto_mode = False
                    waves.clear()
                    sonar_pulses.clear()
                    radar_sweeps.clear()
                    reflected_waves.clear()
                    transmitted_waves.clear()
                    for b in action_buttons:
                        if b.action == "AUTO":
                            b.active = False

        # Обработка кнопок материалов
        for button in material_buttons:
            action = button.handle_event(event)
            if action and action in MATERIALS:
                for b in material_buttons:
                    b.active = (b.action == action)
                current_material = action

        # Обработка клавиатуры
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if system_type == "RADIO":
                    waves.append(RadioWave(wave_source, frequency, wave_speed))
                elif system_type == "SONAR":
                    sonar_pulses.append(SonarPulse(sonar_source, frequency * 0.5, wave_speed * 0.8))
                elif system_type == "RADAR":
                    if not radar_sweeps:
                        radar_sweeps.append(RadarSweep(radar_source, 250, 3))
            elif event.key == pygame.K_c:
                waves.clear()
                sonar_pulses.clear()
                radar_sweeps.clear()
                reflected_waves.clear()
                transmitted_waves.clear()
                obstacles.clear()
                current_obstacle_points.clear()
            elif event.key == pygame.K_a:
                auto_mode = not auto_mode
            elif event.key == pygame.K_1:
                system_type = "RADIO"
                for b in system_buttons:
                    b.active = (b.action == system_type)
            elif event.key == pygame.K_2:
                system_type = "SONAR"
                for b in system_buttons:
                    b.active = (b.action == system_type)
            elif event.key == pygame.K_3:
                system_type = "RADAR"
                for b in system_buttons:
                    b.active = (b.action == system_type)

        # Обработка мыши
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Проверяем, что клик не в UI области
            if mouse_x < width - 380:
                if event.button == 1:  # Левая кнопка мыши
                    if mode == "SOURCE":
                        if system_type == "RADIO":
                            wave_source = (mouse_x, mouse_y)
                        elif system_type == "SONAR":
                            sonar_source = (mouse_x, mouse_y)
                        elif system_type == "RADAR":
                            radar_source = (mouse_x, mouse_y)
                            # Перезапускаем радар с новой позиции
                            radar_sweeps.clear()
                            radar_sweeps.append(RadarSweep(radar_source, 250, 3))
                    elif mode == "DRAW":
                        current_obstacle_points.append((mouse_x, mouse_y))

                elif event.button == 3:  # Правая кнопка мыши
                    if mode == "DRAW" and len(current_obstacle_points) >= 3:
                        obstacles.append(Obstacle(current_obstacle_points.copy(), current_material))
                        current_obstacle_points.clear()

    # Автоматический режим
    if auto_mode:
        auto_timer += 1
        if auto_timer >= auto_interval:
            auto_timer = 0
            if system_type == "RADIO":
                waves.append(RadioWave(wave_source, frequency, wave_speed))
            elif system_type == "SONAR":
                sonar_pulses.append(SonarPulse(sonar_source, frequency * 0.5, wave_speed * 0.8))
            elif system_type == "RADAR":
                if not radar_sweeps:
                    radar_sweeps.append(RadarSweep(radar_source, 250, 3))

    # Обновление радиоволн
    for wave in waves[:]:
        wave.update()
        if not wave.active:
            waves.remove(wave)
        else:
            collisions = check_wave_collision(wave, obstacles)
            for collision in collisions:
                material = collision['material']

                if material.reflection > 0.01:
                    reflected_wave = ReflectedWave(
                        collision['point'],
                        collision['direction'],
                        frequency,
                        wave_speed,
                        material.reflection
                    )
                    reflected_waves.append(reflected_wave)

                if material.transmission > 0.01:
                    incident_direction = (
                        collision['point'][0] - wave.origin[0],
                        collision['point'][1] - wave.origin[1]
                    )
                    length = math.sqrt(incident_direction[0] ** 2 + incident_direction[1] ** 2)
                    if length > 0:
                        normalized_direction = (incident_direction[0] / length, incident_direction[1] / length)

                        transmission_origin = (
                            collision['point'][0] + normalized_direction[0] * 20,
                            collision['point'][1] + normalized_direction[1] * 20
                        )

                        transmitted_wave = TransmittedWave(
                            transmission_origin,
                            normalized_direction,
                            frequency,
                            wave_speed,
                            material.transmission
                        )
                        transmitted_waves.append(transmitted_wave)

    # Обновление сонара
    for pulse in sonar_pulses[:]:
        pulse.update(obstacles)
        if not pulse.active:
            sonar_pulses.remove(pulse)

    # Обновление радара
    for radar in radar_sweeps[:]:
        radar.update(obstacles)

    # Обновление отражённых и прошедших волн
    for wave in reflected_waves[:]:
        wave.update()
        if not wave.active:
            reflected_waves.remove(wave)

    for wave in transmitted_waves[:]:
        wave.update()
        if not wave.active:
            transmitted_waves.remove(wave)

    # Отрисовка
    screen.fill((0, 0, 0))

    # Рисуем препятствия
    for obstacle in obstacles:
        obstacle.draw(screen)

    # Рисуем текущее препятствие в процессе создания
    if len(current_obstacle_points) > 0:
        if len(current_obstacle_points) == 1:
            pygame.draw.circle(screen, (255, 255, 0), current_obstacle_points[0], 3)
        else:
            pygame.draw.lines(screen, (255, 255, 0), False, current_obstacle_points, 2)
            for point in current_obstacle_points:
                pygame.draw.circle(screen, (255, 255, 0), point, 3)

    # Рисуем волны
    for wave in waves:
        wave.draw(screen)

    for pulse in sonar_pulses:
        pulse.draw(screen)

    for radar in radar_sweeps:
        radar.draw(screen)

    for wave in reflected_waves:
        wave.draw(screen)

    for wave in transmitted_waves:
        wave.draw(screen)

    # Рисуем источники
    # Источник радиоволн (белый с красной границей)
    pygame.draw.circle(screen, (255, 255, 255), wave_source, 8)
    pygame.draw.circle(screen, (255, 0, 0), wave_source, 8, 2)
    source_text = small_font.render("R", True, (255, 0, 0))
    text_rect = source_text.get_rect(center=(wave_source[0], wave_source[1] - 20))
    screen.blit(source_text, text_rect)

    # Источник сонара (синий)
    pygame.draw.circle(screen, (100, 100, 255), sonar_source, 8)
    pygame.draw.circle(screen, (0, 0, 255), sonar_source, 8, 2)
    sonar_text = small_font.render("S", True, (0, 0, 255))
    text_rect = sonar_text.get_rect(center=(sonar_source[0], sonar_source[1] - 20))
    screen.blit(sonar_text, text_rect)

    # Источник радара (жёлтый)
    pygame.draw.circle(screen, (255, 255, 100), radar_source, 8)
    pygame.draw.circle(screen, (255, 255, 0), radar_source, 8, 2)
    radar_text = small_font.render("A", True, (255, 255, 0))
    text_rect = radar_text.get_rect(center=(radar_source[0], radar_source[1] - 20))
    screen.blit(radar_text, text_rect)

    # Рисуем обнаружения сонара
    for pulse in sonar_pulses:
        for detection in pulse.detections:
            point = detection['point']
            # Рисуем линию от сонара к обнаруженному объекту
            pygame.draw.line(screen, (0, 255, 255), pulse.origin, point, 1)
            # Мигающий маркер
            if int(time.time() * 3) % 2:
                pygame.draw.circle(screen, (0, 255, 255), (int(point[0]), int(point[1])), 6, 2)

    # Рисуем UI
    draw_ui(screen)

    # Инструкции в нижней части экрана
    instructions = [
        "Горячие клавиши: SPACE - импульс, C - очистить, A - авто режим, 1-3 - тип системы",
        "ЛКМ - выбор источника/рисование, ПКМ - завершить фигуру"
    ]

    for i, instruction in enumerate(instructions):
        instr_text = small_font.render(instruction, True, (150, 150, 150))
        screen.blit(instr_text, (10, height - 35 + i * 18))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()