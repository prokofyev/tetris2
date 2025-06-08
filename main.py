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
GAP_BETWEEN_GRIDS = 4  # Расстояние между стаканами
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH * 2 + GAP_BETWEEN_GRIDS)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT
LEFT_GRID_OFFSET = 0
RIGHT_GRID_OFFSET = BLOCK_SIZE * (GRID_WIDTH + GAP_BETWEEN_GRIDS)
GAME_OVER_MESSAGE_DURATION = 3000  # 3 секунды в миллисекундах

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

class Player:
    def __init__(self, grid_offset, controls):
        self.grid_offset = grid_offset
        self.controls = controls
        self.reset()
        self.score = 0
    
    def reset(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece_idx = 0
        self.current_piece = None
        self.game_over = False
        self.fall_time = 0 

class Controls:
    def __init__(self, left, right, down, rotate, drop):
        self.left = left
        self.right = right
        self.down = down
        self.rotate = rotate
        self.drop = drop

class Tetris:
    def __init__(self):
        self.piece_sequence = []
        self.left_player = Player(LEFT_GRID_OFFSET, 
            Controls(pygame.K_a, pygame.K_d, pygame.K_s, pygame.K_w, pygame.K_LSHIFT))
        self.right_player = Player(RIGHT_GRID_OFFSET,
            Controls(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_UP, pygame.K_SPACE))
        self.game_over_timer = 0
        self.fall_speed = 0.5
        self.reset_game()
        
    def reset_game(self):
        self.piece_sequence = self.generate_piece_sequence(100)  # Генерируем 100 фигур вперед
        self.left_player.reset()
        self.left_player.current_piece = self.get_new_current_piece(self.left_player)
        self.right_player.reset()
        self.right_player.current_piece = self.get_new_current_piece(self.right_player)
        self.state = GameState.PLAYING
    
    def generate_piece_sequence(self, length):
        r = []
        for _ in range(length):
            shape = random.choice(SHAPES)
            r.append({
            "shape": shape,
            "color": COLORS[SHAPES.index(shape)]
        })
        return r

    def get_new_current_piece(self, player):
        piece = self.piece_sequence[player.current_piece_idx].copy()
        piece["x"] = GRID_WIDTH // 2 - len(piece["shape"][0]) // 2
        piece["y"] = 0
        return piece
    
    def valid_move(self, player, piece, x_offset=0, y_offset=0):
        """Проверяет возможность движения фигуры"""
        for y, row in enumerate(piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece["x"] + x + x_offset
                    new_y = piece["y"] + y + y_offset
                    
                    if (new_x < 0 or new_x >= GRID_WIDTH or 
                        new_y >= GRID_HEIGHT or 
                        (new_y >= 0 and player.grid[new_y][new_x])):
                        return False
        return True
    
    def rotate_piece(self, player):
        """Вращает фигуру вокруг центра с автоматической коррекцией у границ"""
        current_piece = player.current_piece
        old_shape = current_piece["shape"]
        old_x, old_y = current_piece["x"], current_piece["y"]
        
        # Вычисляем центр вращения
        center_x = old_x + len(old_shape[0]) / 2
        center_y = old_y + len(old_shape) / 2
        
        # Поворачиваем матрицу
        rotated = [list(row) for row in zip(*old_shape[::-1])]
        current_piece["shape"] = rotated
        
        # Новая позиция для сохранения центра
        new_x = round(center_x - len(rotated[0]) / 2)
        new_y = round(center_y - len(rotated) / 2)

        # Пробуем разные смещения при невозможности поворота
        for dx, dy in [(0,0), (-1,0), (1,0), (-2,0), (2,0)]:  # Возможные коррекции
            current_piece["x"] = new_x + dx
            current_piece["y"] = new_y + dy
            if self.valid_move(player, current_piece, 0, 0):
                return True
        
        # Если никакая коррекция не помогла - откат
        current_piece["shape"] = old_shape
        current_piece["x"], current_piece["y"] = old_x, old_y
        return False  
        
    def clear_lines(self, player):
        for y in range(GRID_HEIGHT):
            if all(player.grid[y]):
                for y2 in range(y, 0, -1):
                    player.grid[y2] = player.grid[y2-1][:]
                player.grid[0] = [0 for _ in range(GRID_WIDTH)]
    
    def update(self, delta_time):
        if self.state != GameState.PLAYING:
            if self.state == GameState.GAME_OVER:
                self.game_over_timer += delta_time * 1000  # конвертируем в миллисекунды
                if self.game_over_timer >= GAME_OVER_MESSAGE_DURATION:
                    self.reset_game()
            return
        
        self.update_player(self.left_player, delta_time)
        self.update_player(self.right_player, delta_time)

    def update_player(self, player, delta_time):
        if player.game_over:
            return
            
        # Обновление падения фигуры
        player.fall_time += delta_time
        if player.fall_time >= self.fall_speed:
            player.fall_time = 0
            current_piece = player.current_piece
            if self.valid_move(player, current_piece, 0, 1):
                current_piece["y"] += 1
            else:
                self.lock_piece(player)

    def handle_game_over(self, losing_player):
        winning_player = self.right_player if losing_player == self.left_player else self.left_player
        winning_player.score += 1
        self.state = GameState.GAME_OVER
        self.game_over_timer = 0
    
    def lock_piece(self, player):
        """Фиксирует текущую фигуру в сетке игрока"""
        current_piece = player.current_piece
        for y, row in enumerate(current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    player.grid[current_piece["y"] + y][current_piece["x"] + x] = current_piece["color"]
        
        self.clear_lines(player)
        self.set_current_piece(player)
        
        if not self.valid_move(player, player.current_piece):
            player.game_over = True
            self.handle_game_over(player)
    
    def set_current_piece(self, player):
        """Устанавливает следующую фигуру в качестве текущей"""
        player.current_piece_idx += 1
        if player.current_piece_idx >= len(self.piece_sequence):
            self.piece_sequence.extend(self.generate_piece_sequence(100))
        player.current_piece = self.get_new_current_piece(player)

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
        screen.fill(BLACK)
        
        # Рисуем стаканы и фигуры
        self.draw_player_grid(self.left_player)
        self.draw_player_grid(self.right_player)
        
        # Рисуем счет
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Счет: {self.left_player.score} - {self.right_player.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 10))
        
        # Рисуем сообщение о победителе
        if self.state == GameState.GAME_OVER:
            winner = "Правый" if self.left_player.game_over else "Левый"
            message = f"{winner} игрок победил!"
            message_text = font.render(message, True, WHITE)
            screen.blit(message_text, 
                (SCREEN_WIDTH // 2 - message_text.get_width() // 2, 
                 SCREEN_HEIGHT // 2 - message_text.get_height() // 2))

    def draw_player_grid(self, player):
        # Рисуем сетку
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                pygame.draw.rect(screen, GRAY, 
                    (player.grid_offset + x * BLOCK_SIZE, y * BLOCK_SIZE, 
                     BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Рисуем зафиксированные фигуры
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if player.grid[y][x]:
                    pygame.draw.rect(screen, player.grid[y][x],
                        (player.grid_offset + x * BLOCK_SIZE, y * BLOCK_SIZE,
                         BLOCK_SIZE, BLOCK_SIZE))
        
        # Рисуем текущую фигуру
        current_piece = player.current_piece
        for y, row in enumerate(current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, current_piece["color"],
                        (player.grid_offset + (current_piece["x"] + x) * BLOCK_SIZE,
                            (current_piece["y"] + y) * BLOCK_SIZE,
                            BLOCK_SIZE, BLOCK_SIZE))

    def move_piece(self, player, x_offset, y_offset):
        """Перемещает текущую фигуру игрока"""
        current_piece = player.current_piece
        if self.valid_move(player, current_piece, x_offset, y_offset):
            current_piece["x"] += x_offset
            current_piece["y"] += y_offset
            return True
        return False

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

    def drop_piece(self, player):
        """Мгновенно сбрасывает текущую фигуру вниз"""
        current_piece = player.current_piece
        while self.valid_move(player, current_piece, 0, 1):
            current_piece["y"] += 1
        self.lock_piece(player)
        return True
            
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
    # Обработка клавиш левого игрока
    if not game.left_player.game_over:
        if event.key == game.left_player.controls.left:
            game.move_piece(game.left_player, -1, 0)
        elif event.key == game.left_player.controls.right:
            game.move_piece(game.left_player, 1, 0)
        elif event.key == game.left_player.controls.down:
            game.move_piece(game.left_player, 0, 1)
        elif event.key == game.left_player.controls.rotate:
            game.rotate_piece(game.left_player)
        elif event.key == game.left_player.controls.drop:
            game.drop_piece(game.left_player)
    
    # Обработка клавиш правого игрока
    if not game.right_player.game_over:
        if event.key == game.right_player.controls.left:
            game.move_piece(game.right_player, -1, 0)
        elif event.key == game.right_player.controls.right:
            game.move_piece(game.right_player, 1, 0)
        elif event.key == game.right_player.controls.down:
            game.move_piece(game.right_player, 0, 1)
        elif event.key == game.right_player.controls.rotate:
            game.rotate_piece(game.right_player)
        elif event.key == game.right_player.controls.drop:
            game.drop_piece(game.right_player)
    
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