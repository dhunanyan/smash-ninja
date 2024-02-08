import pygame

from config.constants import Y_MAX_VELOCITY

class Physics:
  def __init__(self, game, e_type, pos, size) -> None:
    self.game = game
    self.type = e_type
    self.pos = list(pos)
    self.size = size
    self.velocity = [0, 0]
    self.collisions = {
      'up': False, 
      'down': False, 
      'right': False, 
      'left': False
      }
    self.y_max_velocity = Y_MAX_VELOCITY
    
    #ANIMATION
    self.action = ''
    self.anim_offset = (-3, -3)
    self.flip = False # True=facing_right False=facing_left
    self.set_action('idle')
    
    self.last_movement = [0, 0]
    
  def rect(self):
    return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])  
  
  def set_action(self, action):
    if action == self.action:
      return
    
    self.action = action
    self.animation = self.game.assets[self.type + '/' + self.action].copy()
  
  def update(self, tilemap, movement=(0,0)):
    self.collisions = {
      'up': False, 
      'down': False, 
      'right': False, 
      'left': False
      }
    frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
    
    self.pos[0] += frame_movement[0]
    entity_rect = self.rect()
    for rect in tilemap.physics_rects_around(self.pos):
      if entity_rect.colliderect(rect):
        if frame_movement[0] > 0: #moving right
          entity_rect.right = rect.left
          self.collisions['right'] = True
        if frame_movement[0] < 0:
          entity_rect.left = rect.right
          self.collisions['left'] = True
        self.pos[0] = entity_rect.x
    
    self.pos[1] += frame_movement[1]
    entity_rect = self.rect()
    for rect in tilemap.physics_rects_around(self.pos):
      if entity_rect.colliderect(rect):
        if frame_movement[1] > 0:
          entity_rect.bottom = rect.top
          self.collisions['down'] = True
        if frame_movement[1] < 0:
          entity_rect.top = rect.bottom
          self.collisions['up'] = True
        self.pos[1] = entity_rect.y
    
    if movement[0] > 0:
      self.flip = False
    if movement[0] < 0:
      self.flip = True
    
    self.last_movement = movement
    
    self.velocity[1] = min(self.y_max_velocity, self.velocity[1] + 0.1)
    
    if self.collisions['down'] or self.collisions['up']:
      self.velocity[1] = 0
    
    self.animation.update()
    
  def render(self, surf, offset):
    img = self.animation.img()
    pos_x = self.pos[0] - offset[0] + self.anim_offset[0]
    pos_y = self.pos[1] - offset[1] + self.anim_offset[1]
    entity = pygame.transform.flip(img, self.flip, False)
    
    surf.blit(entity, (pos_x, pos_y))
