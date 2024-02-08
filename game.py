import random
import sys
import math
import pygame

from components.player import Player
from components.tilemap import Tilemap
from components.clouds import Clouds
from components.particle import Particle

from config.utils import load_image, load_images, Animation
from config.constants import SCREEN_HEIGHT, SCREEN_WIDTH, FPS, RENDER_SCALE, LEAF_ANIMATION_INTENSITY, LEFT_VELOCITY

class Game:
  def __init__(self) -> None:
    pygame.init()

    pygame.display.set_caption("Smash Ninja")
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.display = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)) # SCALING UP

    self.clock = pygame.time.Clock()
    
    self.movement = [False, False]
    
    self.assets = {
      'decor': load_images('tiles/decor'),
      'grass': load_images('tiles/grass'),
      'large_decor': load_images('tiles/large_decor'),
      'stone': load_images('tiles/stone'),
      'spawners': load_images('tiles/spawners'),

      'background': load_image('background.png'),
      'clouds': load_images('clouds'),
      
      'player': load_image('entities/player.png'),
      'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
      'player/run': Animation(load_images('entities/player/run'), img_dur=4),
      'player/jump': Animation(load_images('entities/player/jump')),
      'player/slide': Animation(load_images('entities/player/slide')),
      'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
      'particles/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            
      'particles/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
      'particles/light-sparkle': Animation(load_images('particles/light-sparkle'), img_dur=2, loop=False),
      'particles/dark-sparkle': Animation(load_images('particles/dark-sparkle'), img_dur=1, loop=False),
    }
    
    self.clouds = Clouds(self.assets['clouds'], count=16)
    
    self.player = Player(self, (50, 50), (8, 15))
    self.tilemap = Tilemap(self, tile_size=16)

    try:
      self.tilemap.load('./assets/maps/map0.json')
    except FileNotFoundError:
      pass
    
    self.leaf_spawners = []
    # get a list of locations for fancy animation
    for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
      self.leaf_spawners.append(pygame.Rect(
        4 + tree['pos'][0],
        4 + tree['pos'][1],
        23,
        13
      ))
    
    for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
      if spawner['variant'] == 0:
        self.player.pos = spawner['pos']
      else:
        print('enemy')
    
    self.particles = []
    
    #CAMERA
    self.scroll = [0, 0]

  def run(self) -> None:
    while True:
      self.display.blit(self.assets['background'], (0, 0))

      self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / RENDER_SCALE - self.scroll[0]) / 30
      self.scroll[1] += (self.player.rect().centery - self.display.get_height() / RENDER_SCALE - self.scroll[1]) / 30
      render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

      for rect in self.leaf_spawners:
        if random.random() * LEAF_ANIMATION_INTENSITY < rect.width * rect.height:
          pos = (rect.x + random.random() * rect.width,
                 rect.y + random.random() * rect.height)
          self.particles.append(Particle(self, 'leaf', pos, velocity=LEFT_VELOCITY, frame=random.randint(0, 20)))
          

      self.clouds.update()
      self.clouds.render(self.display, offset=render_scroll)
      
      self.tilemap.render(self.display, offset=render_scroll)

      self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
      self.player.render(self.display, offset=render_scroll)
      
      for particle in self.particles.copy():
        kill = particle.update()
        particle.render(self.display, offset=render_scroll)
        if particle.type == 'leaf':
          # NATURAL ANIMATION
          particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
        if kill:
          self.particles.remove(particle)
      
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          sys.exit()
        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_a:
            self.movement[0] = True
          if event.key == pygame.K_d:
            self.movement[1] = True
          if event.key == pygame.K_w:
            self.player.jump()
          if event.key == pygame.K_s:
            self.player.velocity[1] = 3
          if event.key == pygame.K_SPACE:
            self.player.dash()
        if event.type == pygame.KEYUP:
          if event.key == pygame.K_a:
            self.movement[0] = False
          if event.key == pygame.K_d:
            self.movement[1] = False
      
      self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)) # BLIT FOR SCALING UP
      pygame.display.update()
      self.clock.tick(FPS)
      
Game().run()