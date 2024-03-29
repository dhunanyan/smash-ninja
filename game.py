import random
import os
import sys
import math
import pygame

from components.spark import Spark
from components.enemy import Enemy
from components.player import Player
from components.tilemap import Tilemap
from components.clouds import Clouds
from components.particle import Particle

from config.utils import load_image, load_images, Animation
from config.constants import SCREEN_PROPORTION, SCREEN_SIZE_OPTIONS, FPS, RENDER_SCALE, LEAF_ANIMATION_INTENSITY, LEFT_VELOCITY, PLAYER_DIM, ENEMY_DIM, TRANSITION_COLOR, TRANSITION_SPEED, BACKGROUND_SHADOWS_LIST, SFX_VOLUMES, MUSIC_VOLUMES

class Game:
  def __init__(self) -> None:
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    
    pygame.init()
    pygame.display.set_caption("Smash Ninja")
    
    self.display_info = pygame.display.Info()
    
    self.current_screen_size = [
      self.display_info.current_w,
      self.display_info.current_h
    ]
    self.screen_size = SCREEN_SIZE_OPTIONS['large']
    self.width = self.screen_size['width']
    self.height = self.screen_size['height']
    self.scale = self.screen_size['scale']
    
    self.screen = pygame.display.set_mode((
      self.width, 
      self.height
    ), pygame.RESIZABLE)
    self.display = pygame.Surface((
      self.width / self.scale, 
      self.height / self.scale
    ), pygame.SRCALPHA)
    self.display_2 = pygame.Surface((
      self.width / self.scale, 
      self.height / self.scale
    ))

    self.clock = pygame.time.Clock()
    
    self.movement = [False, False]
    
    self.assets = {
      'decor': load_images('tiles/decor'),
      'grass': load_images('tiles/grass'),
      'large_decor': load_images('tiles/large_decor'),
      'stone': load_images('tiles/stone'),

      'background': load_image('background.png'),
      'clouds': load_images('clouds'),
      
      'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
      'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
      'gun': load_image('gun.png'),
      'projectile': load_image('projectile.png'),
      
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
    player_pos = (50, 50)
    self.clouds = Clouds(self.assets['clouds'], count=16)
    
    self.player = Player(self, player_pos, PLAYER_DIM)
    self.tilemap = Tilemap(self, tile_size=16)

    self.level = 0
    self.music = 0
    self.change_music = True
    self.load_level(self.level)
    
    self.screen_shake = 0
    
    self.sfx = {
      'jump': pygame.mixer.Sound('assets/sfx/jump.wav'),
      'dash': pygame.mixer.Sound('assets/sfx/dash.wav'),
      'hit': pygame.mixer.Sound('assets/sfx/hit.wav'),
      'shoot': pygame.mixer.Sound('assets/sfx/shoot.wav'),
      'ambience': pygame.mixer.Sound('assets/sfx/ambience.wav'),
    }
    
    # Audio volumes
    for sfx in list(self.sfx):
      self.sfx[sfx].set_volume(SFX_VOLUMES[sfx])

  def set_screen_size(self, size: str) -> None:
    self.screen_size = SCREEN_SIZE_OPTIONS[size]

  def set_background_image(self, asset: str) -> None:
    self.background_image = pygame.transform.scale(
      self.assets[asset], (
        self.width / self.scale,
        self.height / self.scale
      )
    )
  
  def load_level(self, map_id):
    self.tilemap.load(f"assets/maps/{map_id}.json")
    
    self.leaf_spawners = []
    # get a list of locations for fancy animation
    tress = self.tilemap.extract([('large_decor', 2)], keep=True)
    for tree in tress:
      self.leaf_spawners.append(pygame.Rect(
        4 + tree['pos'][0],
        4 + tree['pos'][1],
        23,
        13
      ))
    
    self.enemies = []
    # get a list of locations for enemies
    spawners = self.tilemap.extract([
      ('spawners', 0), 
      ('spawners', 1)
    ])
    for spawner in spawners:
      if spawner['variant'] == 0:
        self.player.pos = spawner['pos']
        self.player.air_time = 0
      else:
        self.enemies.append(Enemy(self, spawner['pos'], ENEMY_DIM))
    
    self.projectiles = []
    self.particles = []
    self.sparks = []
    
    self.scroll = [0, 0]
    self.dead = 0
    self.transition = -30
    self.background_image = pygame.transform.scale(
      self.assets['background'], (
        self.width / self.scale,
        self.height / self.scale
      )
    )
  
  def run(self) -> None:
    self.sfx['ambience'].play(-1)
    
    while True:
      if self.change_music:
        pygame.mixer.music.load(f"assets/soundtracks/{min(self.level, len(os.listdir('assets/soundtracks')) - 1)}.wav")
        pygame.mixer.music.set_volume(MUSIC_VOLUMES[self.level])
        pygame.mixer.music.play(-1)
        self.change_music = False
        
      self.display.fill((0, 0, 0, 0))
      self.display_2.blit(self.background_image, (0, 0))
      
      self.screen_shake = max(0, self.screen_shake - 1)
      
      # Game end condition
      if not len(self.enemies):
        self.transition += 1
        if self.transition > 30:
          self.level = min(self.level + 1, len(os.listdir('assets/maps')) - 1)
          self.change_music = True
          self.load_level(self.level)
      if self.transition < 0:
        self.transition += 1
      
      if self.dead:
        self.dead += 1
        if self.dead >= 10:
          self.transition = min(30, self.transition + 1)
        if self.dead > 40:
          self.load_level(self.level)

      self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / RENDER_SCALE - self.scroll[0]) / 30
      self.scroll[1] += (self.player.rect().centery - self.display.get_height() / RENDER_SCALE - self.scroll[1]) / 30
      render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

      for rect in self.leaf_spawners:
        if random.random() * LEAF_ANIMATION_INTENSITY < rect.width * rect.height:
          pos = (rect.x + random.random() * rect.width,
                 rect.y + random.random() * rect.height)
          self.particles.append(Particle(self, 'leaf', pos, velocity=LEFT_VELOCITY, frame=random.randint(0, 20)))
          
      self.clouds.update()
      # self.display_2 instead of self.display to not render outlines of clouds
      self.clouds.render(self.display_2, offset=render_scroll)
      
      self.tilemap.render(self.display, offset=render_scroll)
      
      for enemy in self.enemies.copy():
        kill =enemy.update(self.tilemap, (0, 0))
        enemy.render(self.display, offset=render_scroll)
        if kill:
          self.enemies.remove(enemy)
      
      if not self.dead:
        self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
        self.player.render(self.display, offset=render_scroll)
      
      # [[x, y], direction, timer]
      for projectile in self.projectiles.copy():
        projectile[0][0] += projectile[1]
        projectile[2] += 1
        img = self.assets['projectile']
        self.display.blit(img, (
          projectile[0][0] - img.get_width() / 2 - render_scroll[0],
          projectile[0][1] - img.get_height() / 2 - render_scroll[1]
        ))
        if self.tilemap.solid_check(projectile[0]):
          self.projectiles.remove(projectile)
          for _ in range(4):
            spark = Spark(
              projectile[0],
              random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), # bounce back to the direction it came from
              2 + random.random()
            )
            self.sparks.append(spark)
        elif projectile[2] > 360:
          self.projectiles.remove(projectile)
        elif abs(self.player.dashing) < 50:
          if self.player.rect().collidepoint(projectile[0]):
            self.projectiles.remove(projectile)
            self.dead += 1
            self.sfx['shoot'].play()
            self.screen_shake = max(16, self.screen_shake)
            #EXPLOSION
            for _ in range(30):
              angle = random.random() * math.pi * 2
              speed = random.random() * 5
              spark = Spark(
                self.player.rect().center,
                angle,
                2 + random.random()
              )
              self.sparks.append(spark)
              particle = Particle(
                self,
                'particle',
                self.player.rect().center,
                velocity=[
                  math.cos(angle + math.pi) * speed * 0.5,
                  math.sin(angle + math.pi) * speed * 0.5,
                ],
                frame=random.randint(0, 7)
              )
              self.particles.append(particle)
      
      for spark in self.sparks.copy():
        self.kill = spark.update()
        spark.render(self.display, offset=render_scroll)
        if self.kill:
          self.sparks.remove(spark)
      
      display_mask = pygame.mask.from_surface(self.display)
      display_sillhouette = display_mask.to_surface(
        setcolor=(0, 0, 0, 180), 
        unsetcolor=(0, 0, 0, 0)
      )
      for offset in BACKGROUND_SHADOWS_LIST:
        self.display_2.blit(display_sillhouette, offset)
      
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
        if event.type == pygame.VIDEORESIZE:
          self.width = self.current_screen_size[0]
          self.height = self.current_screen_size[0] / SCREEN_PROPORTION
        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_a:
            self.movement[0] = True
          if event.key == pygame.K_d:
            self.movement[1] = True
          if event.key == pygame.K_w:
            if self.player.jump():
              self.sfx['jump'].play()
          if event.key == pygame.K_s:
            self.player.velocity[1] = 3
          if event.key == pygame.K_SPACE:
            self.player.dash()
        if event.type == pygame.KEYUP:
          if event.key == pygame.K_a:
            self.movement[0] = False
          if event.key == pygame.K_d:
            self.movement[1] = False
      
      if self.transition:
        transition_surf = pygame.Surface(self.display.get_size())
        pygame.draw.circle(
          transition_surf, 
          TRANSITION_COLOR, 
          (self.display.get_width() // 2, self.display.get_height() // 2),
          (TRANSITION_SPEED - abs(self.transition)) * (self.height / TRANSITION_SPEED / 2)
        )
        transition_surf.set_colorkey(TRANSITION_COLOR)
        self.display.blit(transition_surf, (0, 0))
      
      
      self.display_2.blit(self.display, (0, 0))
      
      screen_shake_offset = (
        random.random() * self.screen_shake - self.screen_shake / 2,
        random.random() * self.screen_shake - self.screen_shake / 2,
      )
      print(self.screen.get_size())
      self.screen.blit(pygame.transform.scale(
        self.display_2, (
          self.width,
          self.height
        )
      ), screen_shake_offset) # BLIT FOR SCALING UP
      pygame.display.update()
      self.clock.tick(FPS)
      
Game().run()
