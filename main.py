import pygame
import random
from enum import Enum

# Инициализация pygame
pygame.init()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
COLORS = [
    (0, 255, 255),  # I - голубой
    (0, 0, 255),    # J - синий
    (255, 165, 0),  # L - оранжевый
    (255, 255, 0),  # O - желтый
    (0, 255, 0),    # S - зеленый
    (128, 0, 128),  # T - фиолетовый
    (255, 0, 0)     # Z - красный
]

# Настройки игры
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 6)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT
GAME_AREA_LEFT = BLOCK_SIZE

# Фигуры тетрамино
SHAPES = [
    [[1, 1, 1, 1]],  # I
    
    [[1, 0, 0],
     [1, 1, 1]],     # J
     
    [[0, 0, 1],
     [1, 1, 1]],     # L
     
    [[1, 1],
     [1, 1]],        # O
     
    [[0, 1, 1],
     [1, 1, 0]],     # S
     
    [[0, 1, 0],
     [1, 1, 1]],     # T
     
    [[1, 1, 0],
     [0, 1, 1]]      # Z
]

# Состояния игры
class GameState(Enum):
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3

# Создание экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Тетрис")

# Часы для управления FPS
clock = pygame.time.Clock()

class Tetris:
    def __init__(self):
        self.reset_game()
        
    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.fall_speed = 0.5
        self.fall_time = 0
    
    def new_piece(self):
        shape = random.choice(SHAPES)
        color = COLORS[SHAPES.index(shape)]
        x = GRID_WIDTH // 2 - len(shape[0]) // 2
        y = 0
        return {"shape": shape, "color": color, "x": x, "y": y}
    
    def valid_move(self, piece, x_offset=0, y_offset=0):
        for y, row in enumerate(piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece["x"] + x + x_offset
                    new_y = piece["y"] + y + y_offset
                    
                    if (new_x < 0 or new_x >= GRID_WIDTH or 
                        new_y >= GRID_HEIGHT or 
                        (new_y >= 0 and self.grid[new_y][new_x])):
                        return False
        return True
    
    def rotate_piece(self):
        """Вращает фигуру вокруг центра с автоматической коррекцией у границ"""
        old_shape = self.current_piece["shape"]
        old_x, old_y = self.current_piece["x"], self.current_piece["y"]
        
        # Вычисляем центр вращения
        center_x = old_x + len(old_shape[0]) / 2
        center_y = old_y + len(old_shape) / 2
        
        # Поворачиваем матрицу
        rotated = [list(row) for row in zip(*old_shape[::-1])]
        self.current_piece["shape"] = rotated
        
        # Новая позиция для сохранения центра
        new_x = round(center_x - len(rotated[0]) / 2)
        new_y = round(center_y - len(rotated) / 2)
        
        # Пробуем разные смещения при невозможности поворота
        for dx, dy in [(0,0), (-1,0), (1,0), (-2,0), (2,0)]:  # Возможные коррекции
            self.current_piece["x"] = new_x + dx
            self.current_piece["y"] = new_y + dy
            if self.valid_move(self.current_piece):
                return True
        
        # Если никакая коррекция не помогла - откат
        self.current_piece["shape"] = old_shape
        self.current_piece["x"], self.current_piece["y"] = old_x, old_y
        return False        
        
    def clear_lines(self):
        lines_cleared = 0
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_cleared += 1
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2-1][:]
                self.grid[0] = [0 for _ in range(GRID_WIDTH)]
        
        if lines_cleared == 1:
            self.score += 100 * self.level
        elif lines_cleared == 2:
            self.score += 300 * self.level
        elif lines_cleared == 3:
            self.score += 500 * self.level
        elif lines_cleared == 4:
            self.score += 800 * self.level
        
        self.level = 1 + self.score // 5000
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
    
    def update(self, delta_time):
        if self.state != GameState.PLAYING:
            return
        
        self.fall_time += delta_time
        
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if self.valid_move(self.current_piece, 0, 1):
                self.current_piece["y"] += 1
            else:
                self.lock_piece()
    
    def lock_piece(self):
        for y, row in enumerate(self.current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece["y"] + y][self.current_piece["x"] + x] = self.current_piece["color"]
        
        self.clear_lines()
        self.current_piece = self.new_piece()
        
        if not self.valid_move(self.current_piece):
            self.state = GameState.GAME_OVER
    
    def draw_grid(self):
        """Рисует игровую сетку"""
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                pygame.draw.rect(screen, GRAY, 
                            (GAME_AREA_LEFT + x * BLOCK_SIZE, y * BLOCK_SIZE, 
                                BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_locked_pieces(self):
        """Рисует уже зафиксированные фигуры"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    pygame.draw.rect(screen, self.grid[y][x], 
                                (GAME_AREA_LEFT + x * BLOCK_SIZE, y * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                (GAME_AREA_LEFT + x * BLOCK_SIZE, y * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_current_piece(self):
        """Рисует текущую падающую фигуру"""
        for y, row in enumerate(self.current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, self.current_piece["color"], 
                                (GAME_AREA_LEFT + (self.current_piece["x"] + x) * BLOCK_SIZE, 
                                    (self.current_piece["y"] + y) * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                (GAME_AREA_LEFT + (self.current_piece["x"] + x) * BLOCK_SIZE, 
                                    (self.current_piece["y"] + y) * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_score_info(self):
        """Рисует информацию о счете и уровне"""
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Счет: {self.score}", True, WHITE)
        level_text = font.render(f"Уровень: {self.level}", True, WHITE)
        screen.blit(score_text, (GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 10, 30))
        screen.blit(level_text, (GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 10, 70))

    def draw_pause_screen(self):
        """Рисует экран паузы"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        pause_font = pygame.font.SysFont(None, 64)  # Увеличили размер шрифта
        pause_text = pause_font.render("ПАУЗА", True, WHITE)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 
                                SCREEN_HEIGHT // 2 - 100))  # Подняли ещё выше
        
        restart_font = pygame.font.SysFont(None, 36)
        continue_text = restart_font.render("ESC - продолжить", True, WHITE)
        quit_text = restart_font.render("Пробел - выход", True, WHITE)
        
        screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 
                                SCREEN_HEIGHT // 2 - 10))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 
                            SCREEN_HEIGHT // 2 + 30))

    def draw_game_over_screen(self):
        """Рисует экран окончания игры"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.SysFont(None, 64)  # Увеличили размер шрифта
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, WHITE)  # Без восклицательного знака
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                    SCREEN_HEIGHT // 2 - 100))  # Подняли выше
        
        restart_font = pygame.font.SysFont(None, 36)
        restart_text = restart_font.render("Пробел - новая игра", True, WHITE)
        quit_text = restart_font.render("ESC - выход", True, WHITE)
        
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                                SCREEN_HEIGHT // 2 - 10))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 
                            SCREEN_HEIGHT // 2 + 30))

    def draw(self):
        """Основная функция отрисовки игры"""
        screen.fill(BLACK)
        
        # Рисуем основные элементы игры
        self.draw_grid()
        self.draw_locked_pieces()
        if self.state == GameState.PLAYING:
            self.draw_current_piece()
        self.draw_score_info()
        
        # Рисуем специальные экраны в зависимости от состояния
        if self.state == GameState.PAUSED:
            self.draw_pause_screen()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over_screen()

    def move_left(self):
        """Перемещает фигуру влево, если это возможно"""
        if self.valid_move(self.current_piece, -1, 0):
            self.current_piece["x"] -= 1
    
    def move_right(self):
        """Перемещает фигуру вправо, если это возможно"""
        if self.valid_move(self.current_piece, 1, 0):
            self.current_piece["x"] += 1
    
    def move_down(self):
        """Перемещает фигуру вниз, если это возможно"""
        if self.valid_move(self.current_piece, 0, 1):
            self.current_piece["y"] += 1
            return True
        return False
    
    def drop(self):
        """Мгновенно опускает фигуру вниз"""
        while self.move_down():
            pass
        self.lock_piece()
            
def handle_game_events(game):
    """Обработка событий игры"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if not handle_key_events(game, event):
                return False
    return True

def handle_key_events(game, event):
    """Обработка нажатий клавиш"""
    # Управление в зависимости от состояния игры
    if game.state == GameState.PLAYING:
        return handle_gameplay_keys(game, event)
    elif game.state == GameState.PAUSED:
        return handle_pause_keys(game, event)
    else:  # GAME_OVER
        return handle_gameover_keys(game, event)

def handle_gameplay_keys(game, event):
    """Обработка клавиш во время игры"""
    if event.key == pygame.K_LEFT:
        game.move_left()
    elif event.key == pygame.K_RIGHT:
        game.move_right()
    elif event.key == pygame.K_DOWN:
        game.move_down()
    elif event.key == pygame.K_UP:
        game.rotate_piece()
    elif event.key == pygame.K_SPACE:
        game.drop()
    elif event.key == pygame.K_ESCAPE:
        game.state = GameState.PAUSED
    return True

def handle_pause_keys(game, event):
    """Обработка клавиш в меню паузы"""
    if event.key == pygame.K_ESCAPE:
        game.state = GameState.PLAYING
        return True
    elif event.key == pygame.K_SPACE:
        return False  # Выход из игры
    return True

def handle_gameover_keys(game, event):
    """Обработка клавиш после game over"""
    if event.key == pygame.K_SPACE:
        game.reset_game()
        return True
    elif event.key == pygame.K_ESCAPE:
        return False  # Выход из игры
    return True

def main_game_loop():
    """Главный игровой цикл"""
    game = Tetris()
    running = True
    
    while running:
        delta_time = clock.tick(60) / 1000.0
        
        # Обработка событий
        running = handle_game_events(game)
        
        # Игровая логика
        game.update(delta_time)
        
        # Отрисовка
        game.draw()
        pygame.display.flip()
    
    pygame.quit()

# Запуск игры
if __name__ == "__main__":
    main_game_loop()