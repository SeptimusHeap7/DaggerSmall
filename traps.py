import dungeon
import random
from ursina import *
class Trap(Entity):
    def __init__(self,active,damage,color,position):
        super().__init__(
        model = 'cube',
        collider = 'box',
        color = color,
        scale = 1,

        )
        self.active = active
        self.damage = damage
        self.position = position,
        self.traps_python = []