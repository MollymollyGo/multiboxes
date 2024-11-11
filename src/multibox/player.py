import pygame
import uuid
import math

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.angle = 45
        self.size = 10
        self.id = str(uuid.uuid4())
        self.surface = pygame.Surface((self.size, self.size))
        self.surface.fill((255, 255, 255))

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def set_rotation(self, angle):
        self.angle = math.degrees(angle)

    def set_velocity(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        surf = pygame.transform.rotate(self.surface.convert_alpha(), self.angle)
        rect = surf.get_rect(center=(self.x, self.y))
        screen.blit(surf, rect)
