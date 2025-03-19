import pygame, random
from typing import Literal

pygame.init()

get_val = lambda check, *vals: next((val[1] for val in vals if check == val[0]), None)

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

    def change_size(self, size: pygame.Vector2):
        self.size = size
        self.rect.update(self.loc, size)
        return self

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
    def __init__(
        self,
        coords: pygame.Vector2,
        size: pygame.Vector2 = pygame.Vector2(10)
    ):
        super().__init__(coords, color=pygame.Color(255, 0, 0), size=size)

    def draw(self, main_screen):
        pygame.draw.rect(main_screen, self.color, self.rect)
        return self

    def relocate(self, win_size: pygame.Vector2):
        avail_rect = pygame.Rect(pygame.Vector2(0), win_size)
        avail_rect.inflate_ip(-10, -10)
        new_coords = pygame.Vector2(
            random.randint(avail_rect.left, avail_rect.right) // self.size.x * 10,
            random.randint(avail_rect.top, avail_rect.bottom) // self.size.y * 10
        )
        self.move_to("vect", coords= new_coords)
        return self

class Snake(BaseObject):
    def __init__(
        self,
        coords: pygame.Vector2,
        start_length: int = 5,
        size: pygame.Vector2 = pygame.Vector2(10)
    ):
        super().__init__(coords, color=pygame.Color(0, 255, 0), size=size)
        self.body = [
            BaseObject(
                pygame.Vector2(self.loc) - pygame.Vector2(i * self.size.x, 0),
                color= pygame.Color(255 if i == 0 else 0, 255, 0)
            ) for i in range(0, start_length)
        ]
        self.body.reverse()
        self.direction = pygame.Vector2(self.size.x, 0)
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

    def check_collision(self, win_bounds: list[pygame.Rect]) -> bool:
        return (
            any(map(lambda part: self.loc == part.loc, self.body[:-2]))
            or any(map(self.rect.colliderect, win_bounds))
        )

    def check_eat(self, apple: Apple) -> bool:
        return self.rect.colliderect(apple.rect)

    def change_direction(self, direction: str):
        x = get_val(direction, ("left", -self.size.x), ("right", self.size.x)) or 0
        y = get_val(direction, ("up", -self.size.y), ("down", self.size.y)) or 0
        if not any(map(lambda x1, y1: x1 - y1 == 0, [x, y], [self.direction.x, self.direction.y])):
            self.direction.update(x,y)
        return self

class Game:
    def __init__(
        self,
        window_size: pygame.Vector2,
        window_title: str = 'Snake Game',
        obj_size: int = 10,
        speed: int = 10
    ):
        self.window = pygame.display.set_mode(window_size)
        self.title = window_title
        pygame.display.set_caption(window_title)
        self.clock = pygame.time.Clock()
        self.speed = speed
        self.snake = Snake(pygame.Vector2(100, 50), size=pygame.Vector2(obj_size))
        self.apple = Apple(pygame.Vector2(0, 0), size=pygame.Vector2(obj_size)).relocate(pygame.Vector2(*window_size))
        self.score = 0
        self.obj_size = obj_size
        self.bounds = [
            pygame.Rect(0, 0, window_size.x, self.obj_size), # top
            pygame.Rect(0, 0, self.obj_size, window_size.y), # left
            pygame.Rect(window_size.x - self.obj_size, 0, self.obj_size, window_size.y), # right
            pygame.Rect(0, window_size.y - self.obj_size, window_size.x, self.obj_size), # bottom
        ]
    
    def quit_game(self):
        pygame.quit()
        raise SystemExit
    
    def gen_text(self, size: int, color: pygame.Color, text: str):
        score_font = pygame.font.SysFont('times new roman', size)
        score_surface = score_font.render(text, True, color)
        return score_surface, score_surface.get_rect()
    
    def show_score(self):
        score_surface, score_rect = self.gen_text(20, pygame.Color(255,255,255), f'Score : {self.score}')
        self.window.blit(score_surface, score_rect)

    def reset_game(self):
        self.snake = Snake(pygame.Vector2(100, 50), size=pygame.Vector2(self.obj_size))
        self.apple = (
            Apple(pygame.Vector2(0, 0), size=pygame.Vector2(self.obj_size))
                .relocate(
                    pygame.Vector2(*self.window.get_size())
                )
        )
        self.score = 0

    def game_over_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_q]: self.quit_game()
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_r, pygame.K_KP_ENTER]:
                        return self.reset_game()
            self.clock.tick(10)

    def game_over(self):
        for i, text in enumerate([
            ("Game Over!"),
            (f'Your Score is: {self.score}'),
            ("Press R or Space to play again")
        ]):
            surface, rect = self.gen_text(20, pygame.Color(255,0,0), text)
            rect.midtop = (self.window.get_width()/2, self.window.get_height()/4 + (40 * i))
            self.window.blit(surface, rect)

        pygame.display.flip()
        self.game_over_loop()

    def run(self):
        self.snake.change_direction("right")

        while True:
            for event in pygame.event.get():
                match event.type:
                    case pygame.QUIT: self.quit_game()

                    case pygame.KEYDOWN:
                        if event.key in [pygame.K_ESCAPE, pygame.K_q]: self.quit_game()

                        self.snake.change_direction(
                            get_val(event.key,
                                (pygame.K_UP, "up"),
                                (pygame.K_DOWN, "down"),
                                (pygame.K_LEFT, "left"),
                                (pygame.K_RIGHT, "right"),
                            )
                        )

            self.snake.move()

            if self.snake.check_eat(self.apple):
                self.snake.grow()
                self.apple.relocate(pygame.Vector2(*self.window.get_size()))
                self.score += 10

            if self.snake.check_collision(self.bounds): self.game_over()

            self.window.fill(pygame.Color(0, 0, 0))

            for obj in [self.snake, self.apple]: obj.draw(self.window)

            self.show_score()
            pygame.display.update()
            self.clock.tick(self.speed)

if __name__ == "__main__":
    Game(pygame.Vector2(720, 480), speed=15).run()