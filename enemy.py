from ursina import *
import random
from player import Player
import math
from ursina import time

class Box:
    def __init__(self, center, size):
        self.center = center
        self.size = size

class Enemy(Entity):
    def __init__(self, position, floor_tiles, wall_tiles, player, speed=1, vision_distance=6, vision_degrees=270,
                 **kwargs):
        super().__init__(
            model = load_model('assets/retro_lowpoly_psx_skeleton.glb'),
            scale=1,
            collider='box',
            position=position,
            **kwargs
        )

        self.speed = 0.5
        self.player = player
        self.floor_tiles = floor_tiles
        self.wall_tiles = wall_tiles
        self.billboard = True
        self.floor_tiles = floor_tiles
        self.wall_tiles = wall_tiles
        self.player = player
        self.state = "wandering"
        self.chase_range = 100
        self.lose_range = 100
        self.health = 5
        self.speed = speed
        self.attack_range = 1
        self.attack_cooldown = 0.5
        self._last_attack_time = 0

        self.vision_distance = 30
        self.vision_degrees = vision_degrees

        self.timer = 0
        self.change = random.uniform(1, 4)
        self.pos_change = Vec3(0, 1, 0)

        self.change_direction()

        # If not on floor tile or below floor, destroy self immediately
        if not self._is_on_floor() or self.position.y < 0.4:
            destroy(self)

    def update(self):

        dir_x = self.player.x - self.x
        dir_z = self.player.z - self.z
        angle_to_player = math.degrees(math.atan2(dir_x, dir_z))
        self.rotation_y = angle_to_player + 180


        if self.can_see_player():
            distance = distance_xz(self.position, self.player.position)
            if distance <= self.attack_range:
                if time.time()-self._last_attack_time >= self.attack_cooldown:
                    self.attack_player()
            else:
                self.move_towards_player()
            # Attack if close enough

        else:
            self.wander()

        if self.health<=0:
            destroy(self)

    def change_direction(self):
        self.rotation_y = random.uniform(0, 360)
        radians = math.radians(self.rotation_y)
        self.pos_change = Vec3(math.sin(radians), 0, math.cos(radians))

    def can_see_player(self):
        direction_to_player = self.player.position - self.position
        distance = direction_to_player.length()
        if distance > self.vision_distance:
            return False

        direction_to_player_norm = direction_to_player.normalized()
        forward = Vec3(math.sin(math.radians(self.rotation_y)), 0, math.cos(math.radians(self.rotation_y)))
        angle = math.degrees(math.acos(forward.dot(direction_to_player_norm)))

        return angle <= self.vision_degrees / 2

    def move_towards_player(self):
            direction = (self.player.position - self.position)
            normalized_direction = direction.normalized()
            self._try_move(normalized_direction)

    def wander(self):
        self._try_move(self.pos_change)

    def _try_move(self, direction):
        move_amount = direction * self.speed * time.dt
        new_pos = self.position + move_amount

        if self._collides_with_walls(new_pos) or not self._is_on_floor(new_pos):
            # Change direction immediately if blocked or would fall off floor
            self.change_direction()
        else:
            self.position = new_pos

    def _collides_with_walls(self, pos):
        enemy_bb = Box(center=pos, size=self.scale)

        for wall in self.wall_tiles:
            if wall.collider:
                wall_bb = Box(center=wall.position, size=wall.scale)
                if self._aabb_overlap(enemy_bb, wall_bb):
                    return True
        return False

    def collides_with_any_wall(self):
        if not self or not self.collider:
            return False
        for wall in self.wall_tiles:
            if not wall or not wall.collider:
                continue
            # Only proceed if collider is valid and has necessary methods
            if hasattr(wall.collider, 'intersects'):
                if self.collider.intersects(wall.collider):
                    return True
        return False

    def _aabb_overlap(self, box1, box2):
        for axis in ['x', 'y', 'z']:
            if abs(getattr(box1.center, axis) - getattr(box2.center, axis)) > (getattr(box1.size, axis) + getattr(box2.size, axis)) / 2:
                return False
        return True

    def _is_on_floor(self, pos=None):
        check_pos = pos if pos is not None else self.position
        # Check if any floor tile is close enough beneath enemy (simple proximity check)
        for floor in self.floor_tiles:
            if (floor.position - Vec3(check_pos.x, floor.position.y, check_pos.z)).length() < (
                    self.scale.x + floor.scale.x) / 2:
                return True
        return False

    def attack_player(self):
        if hasattr(self.player, 'health'):
            self._last_attack_time=time.time()
            self.player.health -= 1
            print(f"Player hit! Health: {self.player.health}")

    def distance_xz(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.z - b.z) ** 2)
