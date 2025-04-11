import curses
import math
import os
import random
import sys
import time


class Citizen():

    def __init__(self, x, y, game_of_life):
        self.address = (x, y)
        self.gol = game_of_life
        self.id = f"citizen_x{x}y{y}"
        self.neighbours = []
        self.am_i_alive = False
        self.shall_i_live = False
        self.alive = self.gol.alive
        self.dead = self.gol.dead

    def __repr__(self):
        return self.id

    def __str__(self):
        return str(self.alive) if self.am_i_alive else str(self.dead)

    @property
    def neighbours_alive(self):
        return len(list(filter(lambda n: n.am_i_alive, self.neighbours)))

    def meet_the_neighbours(self):
        neighbours = []
        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                dx, dy = self.address
                dx += x
                dy += y
                if (x or y) and dx >= 0 and dy >= 0 and dx < self.gol.width and dy < self.gol.height:  # noqa
                    neighbours.append(self.gol.field_of_game[dy][dx])
        self.neighbours = neighbours


class GameOfLife():

    def __init__(self, width, height, init_fill=10):
        self.width = width
        self.height = height
        self._field_of_game = []
        self.alive = "O"
        self.just_born = "o"
        self.dead = " "
        self.just_died = "+"
        self._generation = 0

        self.random_seed()
        self._init_field_of_game(int(100 / init_fill) if init_fill > 1 else 10)

    @property
    def field_of_game(self):
        return self._field_of_game

    @property
    def capacity(self):
        return self.width * self.height

    @property
    def citizens_alive(self):
        return sum([len(list(filter(lambda m: m.am_i_alive, row))) for row in self.field_of_game])

    @property
    def generation(self):
        return self._generation

    @staticmethod
    def random_seed():
        rx, ry = math.modf(time.time())
        random.seed((rx * ry) * 10 ** 6)

    def rule_alive(self, c):
        condition1 = (c.am_i_alive and c.neighbours_alive in [2, 3])
        condition2 = (not c.am_i_alive and c.neighbours_alive == 3)
        random_factor = (random.randint(0, 10000) % 100)
        return (condition1 and random_factor) or (condition2 and random_factor)

    def _neighbourhood(self):
        [list(map(lambda m: m.meet_the_neighbours(), row)) for row in self.field_of_game]

    def _init_field_of_game(self, fill):
        field = []
        for h in range(self.height):
            row = []
            dh = random.choice(range(1, self.height))
            for w in range(self.width):
                citizen = Citizen(w, h, self)
                dw = random.choice(range(1, self.width))
                if h % dh in range(self.height // fill) and w % dw in range(self.width // fill):
                    citizen.am_i_alive = random.choice([True, False])
                row.append(citizen)
            field.append(row)

        self._field_of_game = field
        self._neighbourhood()
        self._generation += 1

    def next_generation(self):
        self.random_seed()
        for row in self.field_of_game:
            list(map(lambda c: setattr(c, "shall_i_live", self.rule_alive(c)), row))
            for citizen in row:
                citizen.alive = self.alive if citizen.am_i_alive else self.just_born
                citizen.dead = self.just_died if citizen.am_i_alive and not citizen.shall_i_live else self.dead  # noqa
                citizen.am_i_alive = citizen.shall_i_live
        self._generation += 1

    def change_size_of_the_game(self, new_width, new_height):
        self.width, self.height = new_width, new_height
        new_field = [[None for w in range(self.width)]
                     for h in range(self.height)]
        for h in range(self.height):
            for w in range(self.width):
                if h < len(self.field_of_game) and w < len(
                        self.field_of_game[h]):
                    new_field[h][w] = self.field_of_game[h][w]
                else:
                    new_field[h][w] = Citizen(w, h, self)
        self._field_of_game = new_field
        self._neighbourhood()


def key_hit(screen):
    try:
        return screen.getkey()
    except Exception:
        return None


GPS = 12.5  # generations per second
INIT_FILL = 33

if __name__ == "__main__":

    scr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    curses.start_color()
    scr.keypad(True)
    scr.nodelay(1)
    scr.clear()
    scr.border()

    fps_shutter_time = 1 / GPS

    screen_y, screen_x = scr.getmaxyx()
    grid_y, grid_x = screen_y - 4, screen_x - 2

    game_of_life = GameOfLife(grid_x, grid_y, init_fill=INIT_FILL)
    
    scr.addstr(screen_y - 3, 1, "-" * (grid_x))
    while game_of_life.citizens_alive and game_of_life.citizens_alive < game_of_life.capacity:
        keypressed = key_hit(scr)
        if keypressed:
            if keypressed.upper() == "R":
                scr.clear()
                scr.border()
                scr.addstr(screen_y - 3, 1, "-" * (grid_x))
                game_of_life = GameOfLife(grid_x, grid_y, init_fill=INIT_FILL)
            elif keypressed.upper() == "Q":
                break

        start_time = time.time()
        screen_y, screen_x = scr.getmaxyx()
        if (screen_x, screen_y) != (grid_x + 2, grid_y + 4):
            grid_x, grid_y = screen_x - 2, screen_y - 4
            scr = curses.initscr()
            scr.clear()
            scr.border()
            scr.addstr(screen_y - 3, 1, "-" * (grid_x))
            game_of_life.change_size_of_the_game(grid_x, grid_y)

        try:
            for row, row_of_citizens in enumerate(game_of_life.field_of_game):
                for column, citizen in enumerate(row_of_citizens):
                    scr.addstr(row + 1, column + 1, str(citizen))

            real_execution = time.time() - start_time
            time.sleep(0 if real_execution > fps_shutter_time else fps_shutter_time - real_execution)
            actual_execution = time.time() - start_time
            scr.addstr(screen_y - 3, 1, "-" * (grid_x))
            status_text = " | ".join([
                f"Members alive: {game_of_life.citizens_alive:5}",
                f"Generation: {game_of_life.generation:5}",
                f"Gen/s: {1 / actual_execution:3.3f}",
                f"Capability [Gen/s]: {1 / real_execution:3.3f}",
                f"Grid size: {grid_x:3} x {grid_y:3}",
                f"Capacity: {game_of_life.capacity:5}"]
            )[:screen_x - 3]
            scr.addstr(screen_y - 2, 2, status_text + " " * (screen_x - len(status_text) - 3))
            scr.refresh()
            game_of_life.next_generation()

        except KeyboardInterrupt:
            break

    curses.endwin()
