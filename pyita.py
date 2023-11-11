
import pygame
import numpy as np
import random
from random import shuffle, choice
from time import sleep, perf_counter

# I've tried cython, numba, multiprocessing but any of these seems to work,
# they tend to slow it even more for whatever reason...
from numba import jit
import multiprocessing as mp

pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont('Futura', 30)

# colors
BACKGROUND_DARK = '#2f2a3c'
BACKGROUND = '#352F44'
DARKER = '#5C5470'
DARK = '#B9B4C7'
BRIGHT_DARK = '#e8d9c9'
BRIGHT = '#FAF0E6'
WATER_DARK = '#c1daf0'
WATER_BRIGHT = '#adcdeb'
SMOKE_DARK = '#5d576b'
SMOKE_BRIGHT = '#888198'

scale = 5
tick = 60

WIDTH, HEIGHT = (1280, 720)
window = pygame.display.set_mode((WIDTH, HEIGHT))
sim_surface = pygame.Surface((WIDTH//scale, HEIGHT//scale))
sim_surface.fill(BACKGROUND)
pygame.display.set_caption('Pyita')


class Particle():

    __slots__ = ['x', 'y', 'type', 'color', 'age', 'chaos', 'direction']

    def __init__(self, type, x, y, color=BRIGHT):
        self.age = perf_counter()
        self.x, self.y = (x, y)
        self.color = color
        self.type = type # sand, water, smoke, etc.
        self.chaos = 0
        self.direction = 0

    def update(self):
        match self.type:

            case 'sand':
                offset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 1]
                particles_grid[self.y, self.x] = 0
                for _ in range(10):
                    o = offset.pop(random.randint(0, len(offset)-1))
                    if not particles_grid[self.y+1, self.x+o]:
                        self.x += o
                        self.y += 1
                        break
                particles_grid[self.y, self.x] = Particle('sand', self.x, self.y, color=self.color)

            case 'water':
                # bunch of rules for water movement, looks trivial but it does the job
                particles_grid[self.y, self.x] = 0

                self.chaos = random.randrange(-1, 2, step=1)

                self.color = choice([WATER_BRIGHT, WATER_DARK])
                #if (self.x, self.y+1) not in particles_set:
                if not particles_grid[self.y+1, self.x]:
                    self.y += 1
                    self.direction = random.randrange(-1, 2, step=2)
                else:
                    if not particles_grid[self.y, self.x + self.chaos]:
                        self.x += self.chaos

                if not particles_grid[self.y, self.x + self.direction]:
                    # check if there's abstacle, then change direction
                    self.direction *= -1

                self.x += self.direction
                particles_grid[self.y, self.x] = Particle('water', self.x, self.y, color=self.color)

            case 'smoke':
                # same logic as water but goes up (y-1)
                self.chaos = random.randrange(-1, 2, step=1)

                self.color = choice([SMOKE_BRIGHT, SMOKE_DARK])
                if (self.x, self.y-1) not in particles_set:
                    self.y -= 1
                    self.direction = random.randrange(-1, 2, step=2)
                else:
                    if (self.x + self.chaos, self.y) not in particles_set:
                        self.x += self.chaos

                if (self.x + self.direction, self.y) in particles_set:
                    # check if there's abstacle, then change direction
                    self.direction *= -1

                self.x += self.direction

    def switch_position(self, obj):
        temp_x, temp_y = self.x, self.y
        self.x, self.y = obj.x, obj.y
        obj.x, obj.y, = temp_x, temp_y


    def draw(self):
        #particles_grid[self.y, self.x] = Particle('sand', self.x, self.y, color=self.color)
        pygame.draw.rect(sim_surface, self.color, (self.x, self.y, 1, 1))

def change_brush():
    global brush
    match brush:
        case 'sand'  : brush = 'water'
        case 'water' : brush = 'smoke'
        case 'smoke' : brush = 'sand'

def draw_frame():
    pygame.draw.rect(sim_surface, DARKER, (0, 0, 256, 1))
    pygame.draw.rect(sim_surface, DARKER, (0, 143, 256, 1))
    pygame.draw.rect(sim_surface, DARKER, (0, 0, 1, 143))
    pygame.draw.rect(sim_surface, DARKER, (255, 0, 1, 143))

def spawn(x, y):
    global particles_arr
    global particles_set
    x = x//scale
    y = y//scale
    if not particles_grid[y, x]:
        match brush:
            case 'sand':
                for size in range(brush_size):
                    particles_grid[y-size, x] = Particle('sand', x, y-size, color=choice([BRIGHT, BRIGHT_DARK]))
            case 'water':
                for size in range(0, brush_size+1):
                    particles_grid[y-size, x] = Particle('water', x, y-size, color=choice([WATER_BRIGHT, WATER_DARK]))
                    #particles_arr.append(Particle('water', x, y-size, color=WATER_BRIGHT))
            case 'smoke':
                for size in range(0, brush_size+1):
                    particles_arr.append(Particle('smoke', x, y-size, color=DARK))


# NOT USED
def despawn(x, y):
    global particles_arr
    global particles_set
    if (x, y) in particles_set:
        for i, p in enumerate(particles_arr):
            if (p.x, p.y) == (x, y):
                particles_arr = np.delete(particles_arr, i)


def update_particles():
    for pix in particles_grid[1:143, 1:255].flatten():
        if pix == 1 or pix == 0: continue
        if all(particles_grid[pix.y + 1, (pix.x - 1):(pix.x + 2)]):
            pix.draw()
            continue
        if pix:
            if pix.type == 'smoke':
                if perf_counter() - pix.age > 10:
                    particles_grid[pix.y][pix.x] == 0
            #if p.type == 'sand':
                #if perf_counter() - p.age < 3:
                    # If time of particle gets above 3 seconds it stops calculating which stops it from any movement
                    # Python is too slow and this is the key optimization trick, I couldn't any find better solution...
                    #p.update()
            #if p.type == 'water':
                #if random.randint(0, 100) < 5:
                    ## 5% chance to update so it don't flick on sreen so much
                #p.update()
            pix.update()
            pix.draw()


def main():
    global brush
    global particles_set
    global particles_arr
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(tick)
        text_fps     = my_font.render(f'FPS: {int(clock.get_fps())}', False, BRIGHT)
        text_counter = my_font.render(f'PIXELS: {np.count_nonzero(particles_grid)}', False, BRIGHT)
        text_tool    = my_font.render(f'TOOL: {brush.upper()} (click to change)', False, BRIGHT)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if pygame.mouse.get_pressed()[0]:
            # spawns particle on left mouse click
            mouse_x = pygame.mouse.get_pos()[0]
            mouse_y = pygame.mouse.get_pos()[1]
            if (20 <= mouse_x < 160) and (80 <= mouse_y < 98):
                change_brush()
            x, y = (pygame.mouse.get_pos()[0],
                    pygame.mouse.get_pos()[1])
            spawn(x, y)


            # NOT FIXED YET
            #if pygame.mouse.get_pressed()[2]:
                #continue
                # remove particle on left mouse click
                #x, y = (pygame.mouse.get_pos()[0],
                #        pygame.mouse.get_pos()[1])
                #despawn(x, y)


        sim_surface.fill(BACKGROUND_DARK)
        draw_frame()

        #particles_grid[1:159, 1:239] = 0

        update_particles()


        window.blit(pygame.transform.scale(sim_surface, (WIDTH, HEIGHT)), (0, 0))
        window.blit(sim_surface, (WIDTH-(WIDTH//scale)-20, 20))
        window.blit(text_fps, (20, 20))
        window.blit(text_counter, (20, 50))
        window.blit(text_tool, (20, 80))
        pygame.display.flip()


brush = 'sand'
particles_grid = np.zeros(36_068, dtype=object).reshape(142, 254)
particles_grid = np.pad(particles_grid, pad_width=1, constant_values=1)
particles_set = ()
water_level = 0
brush_size = 15


#spawn(WIDTH // 2, HEIGHT // 2)


if __name__ == "__main__":
    main()


# Regards, Gracjan :]
