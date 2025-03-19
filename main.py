import pygame, time, random
from typing import Literal

get_val = lambda check, *vals: next((val[1] for val in vals if check == val[0]), None)

snake_speed = 10
window_x = 720
window_y = 480
starting_size = 5

window_bounds = [
    pygame.Rect(0, 0, window_x, 10), # top
    pygame.Rect(0, 0, 10, window_y), # left
    pygame.Rect(window_x - 10, 0, 10, window_y), # right
    pygame.Rect(0, window_y - 10, window_x, 10), # bottom
]

class Sprite:
    def __init__(self, coords: pygame.Vector2, file: str, size: pygame.Vector2):
        self.loc = coords
        self.size = size
        self.rect = pygame.Rect(coords, size)
        self.image = pygame.transform.scale(pygame.image.load(file), size)
    
    def rotate(self, angle: int):
        self.image = pygame.transform.rotate(self.image, angle)
        return self
    
    def hue_shift(self, shift: int):
        self.image = pygame.transform.laplacian(self.image, shift)
        return self

class BaseObject:
    def __init__(self,
        coords: pygame.Vector2, size: pygame.Vector2 = pygame.Vector2(10),
        color: pygame.Color | None = pygame.Color(0, 0, 0),
        sprite: Sprite | None = None
    ):
        self.loc = coords
        self.color = color
        self.sprite = sprite
        self.mode: Literal["color", "sprite"] = "sprite" if sprite is not None else "color"
        self.size = size
        self.rect = pygame.Rect(coords, size)

    def update_mode(self, mode: Literal["color", "sprite"], value: pygame.Color | Sprite):
        self.mode = mode
        match mode:
            case "color": self.color = value
            case "sprite": self.sprite = value
            case _: pass
        return self

    def move_to(
            self, mode: Literal["vect", "coords"],
            x: int | None = None,
            y: int | None = None,
            coords: pygame.Vector2 | None = None
        ):
        match mode:
            case "vect": self.loc.update(coords)
            case "coords": self.loc.update(x, y)
            case _: pass
        self.rect.update(self.loc, self.size)
        return self

class Apple(BaseObject):
    def __init__(self, coords: pygame.Vector2):
        super().__init__(coords, color=pygame.Color(255, 0, 0))

    def draw(self, main_screen):
        pygame.draw.rect(main_screen, self.color, self.rect)
        return self
    
    def relocate(self):
        self.move_to(
            "vect",
            coords= pygame.Vector2(
                random.randint(1, window_x // 10 - 1) * 10,
                random.randint(1, window_y // 10 - 1) * 10
            )
        )
        while any(map(self.rect.colliderect, window_bounds)):
            self.move_to(
                "vect",
                coords= pygame.Vector2(
                    random.randint(1, window_x // 10 - 1) * 10,
                    random.randint(1, window_y // 10 - 1) * 10
                )
            )
        return self

class Snake(BaseObject):
    def __init__(self, coords: pygame.Vector2):
        super().__init__(coords, color=pygame.Color(0, 255, 0))
        self.body = [
            BaseObject(
                pygame.Vector2(self.loc) - pygame.Vector2(i * 10, 0),
                color= pygame.Color(255 if i == 0 else 0, 255, 0)
            ) for i in range(0, starting_size)
        ]
        self.body.reverse()
        self.direction = pygame.Vector2(10, 0)
        self.old_end = self.body[0].loc.copy()

    def draw(self, main_screen: pygame.surface.Surface):
        for part in self.body:
            match part.mode:
                case "sprite": main_screen.blit(part.sprite.image, part.rect)
                case "color": pygame.draw.rect(main_screen, part.color, part.rect)
                case _: pass
        return self

    def move(self):
        self.old_end = self.body[0].loc.copy()
        self.move_to(
            "vect",
            coords= self.loc + self.direction
        )
        for i in range(0, len(self.body) - 1): self.body[i].move_to(
            "vect",
            coords= self.body[i + 1].loc.copy()
        )
        self.body[-1].move_to("vect", coords= self.loc.copy())
        return self

    def grow(self):
        self.body.insert(0, BaseObject(self.old_end, color= pygame.Color(0, 255, 0)))
        return self

    def check_collision(self) -> bool:
        return (
            any(map(lambda part: self.loc == part.loc, self.body[:-2]))
            or any(map(self.rect.colliderect, window_bounds))
        )

    def check_eat(self, apple: Apple) -> bool:
        return self.rect.colliderect(apple.rect)
    
    def change_direction(self, direction: str):
        x = get_val(direction, ("left", -10), ("right", 10)) or 0
        y = get_val(direction, ("up", -10), ("down", 10)) or 0
        if not any(map(lambda x1, y1: x1 - y1 == 0, [x, y], [self.direction.x, self.direction.y])):
            self.direction.update(x,y)
        return self

pygame.init()
pygame.display.set_caption('Snake Game')
game_window = pygame.display.set_mode((window_x, window_y))
fps = pygame.time.Clock()
snake = Snake(pygame.Vector2(100, 50))
apple = Apple(pygame.Vector2(0, 0)).relocate()
score = 0

def gen_text(size, color, text):
    score_font = pygame.font.SysFont('times new roman', size)
    score_surface = score_font.render(text, True, color)
    return score_surface, score_surface.get_rect()

def show_score():
    score_surface, score_rect = gen_text(20, pygame.Color(255,255,255), f'Score : {score}')
    game_window.blit(score_surface, score_rect)

def game_over():
    global snake, apple, score
    game_over_surface, game_over_rect = gen_text(50, pygame.Color(255, 0, 0), f'Your Score is : {score}')
    game_over_rect.midtop = (window_x/2, window_y/4)
    game_window.blit(game_over_surface, game_over_rect)
    pygame.display.flip()
    time.sleep(2)
    snake = Snake(pygame.Vector2(100, 50))
    apple = Apple(pygame.Vector2(0, 0)).relocate()
    score = 0


snake.change_direction("right")

while True:
    moves: list[str] = []
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                pygame.quit()
                raise SystemExit
            case pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    pygame.quit()
                    raise SystemExit
                snake.change_direction(
                    get_val(event.key,
                        (pygame.K_UP, "up"),
                        (pygame.K_DOWN, "down"),
                        (pygame.K_LEFT, "left"),
                        (pygame.K_RIGHT, "right"),
                    )
                )
    snake.move()
    if snake.check_eat(apple):
        snake.grow()
        apple.relocate()
        score += 10
    game_window.fill(pygame.Color(0, 0, 0))
    snake.draw(game_window)
    apple.draw(game_window)
    if snake.check_collision():
        game_over()
    show_score()
    pygame.display.update()
    fps.tick(snake_speed)
