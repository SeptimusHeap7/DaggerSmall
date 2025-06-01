from ursina import *
import random,math,traps

class Dungeon:
    def __init__(self, room_count=10, room_min_size=3, room_max_size=6, tile_size=1, theme=color.light_gray):
        self.room_count = room_count
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.tile_size = tile_size
        self.theme = theme
        self.teleporter = None
        self.traps = []
        self.rooms = []
        self.floor_tiles = []
        self.wall_tiles = []
        self.corridor_tiles = []
        self.door = None
        self.door_open = False
        self.door_direction = None

    def generate_rooms(self):
        self.rooms = []
        for _ in range(self.room_count):
            w = random.randint(self.room_min_size, self.room_max_size)
            h = random.randint(self.room_min_size, self.room_max_size)
            x = random.randint(-10, 10)
            z = random.randint(-10, 10)
            self.rooms.append((x, z, w, h))


    def generate_floor(self):
        for tile in self.floor_tiles:
            destroy(tile)
        self.floor_tiles.clear()

        for (x, z, w, h) in self.rooms:
            for i in range(w):
                for j in range(h):
                    world_x = (x + i) * self.tile_size
                    world_z = (z + j) * self.tile_size
                    floor = Entity(
                        model='cube',
                        color=self.theme,
                        collider='box',
                        scale=(self.tile_size, 0.1, self.tile_size),
                        position=(world_x, 0, world_z)
                    )
                    floor.texture = "assets/hackatanay/floor.png"
                    self.floor_tiles.append(floor)

        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            x1, z1, w1, h1 = self.rooms[i]
            x2, z2, w2, h2 = self.rooms[i + 1]

            cx1 = x1 + w1 // 2
            cz1 = z1 + h1 // 2
            cx2 = x2 + w2 // 2
            cz2 = z2 + h2 // 2

            for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                wx = x * self.tile_size
                wz = cz1 * self.tile_size
                if not self._floor_tile_exists(wx, wz):
                    floor = Entity(
                        model='cube',
                        color=self.theme,
                        collider='box',
                        scale=(self.tile_size, 0.1, self.tile_size),
                        position=(wx, 0, wz)
                    )
                    t = random.randint(0,1)

                    floor.texture = "assets/hackatanay/floor.png"

                    self.floor_tiles.append(floor)
                    self.corridor_tiles.append(floor)

            for z in range(min(cz1, cz2), max(cz1, cz2) + 1):
                wx = cx2 * self.tile_size
                wz = z * self.tile_size
                if not self._floor_tile_exists(wx, wz):
                    floor = Entity(
                        model='cube',
                        color=self.theme,
                        collider='box',
                        scale=(self.tile_size, 0.1, self.tile_size),
                        position=(wx, 0, wz)
                    )
                    floor.texture = "assets/hackatanay/floor.png"

                    self.floor_tiles.append(floor)
                    self.corridor_tiles.append(floor)

    def _floor_tile_exists(self, x, z):
        return any(tile.x == x and tile.z == z for tile in self.floor_tiles)

    def generate_walls(self, preferred_door_direction=None):
        # Clean up old walls and door
        for wall in self.wall_tiles:
            destroy(wall)
        self.wall_tiles.clear()
        if self.door:
            destroy(self.door)
            self.door = None
        self.door_open = False

        floor_positions = {(tile.x, tile.z) for tile in self.floor_tiles}
        wall_height = 2
        ts = self.tile_size

        # Store all valid edge positions to possibly place a door
        candidate_edges = []

        for tile in self.floor_tiles:
            x, z = tile.x, tile.z
            neighbors = {
                'N': (x, z + ts),
                'S': (x, z - ts),
                'E': (x + ts, z),
                'W': (x - ts, z),
            }

            for direction, pos in neighbors.items():
                if pos not in floor_positions:
                    wx, wz = pos
                    wall_pos = None
                    wall_scale = None

                    if direction == 'N':
                        wall_pos = (x, wall_height / 2, z + ts / 2)
                        wall_scale = (ts, wall_height, 0.1)
                    elif direction == 'S':
                        wall_pos = (x, wall_height / 2, z - ts / 2)
                        wall_scale = (ts, wall_height, 0.1)
                    elif direction == 'E':
                        wall_pos = (x + ts / 2, wall_height / 2, z)
                        wall_scale = (0.1, wall_height, ts)
                    elif direction == 'W':
                        wall_pos = (x - ts / 2, wall_height / 2, z)
                        wall_scale = (0.1, wall_height, ts)

                    candidate_edges.append({
                        'pos': wall_pos,
                        'scale': wall_scale,
                        'direction': direction
                    })

        # Choose one candidate to be the door, based on preference if provided
        door_edge = None
        if preferred_door_direction:
            preferred = [c for c in candidate_edges if c['direction'] == preferred_door_direction]
            if preferred:
                door_edge = None
        if not door_edge and candidate_edges:
            door_edge = None
        ra = random.randint(0,1)
        if ra == 0:
            tex = "assets/hackatanay/wall_red.png"
        else:
            tex = "assets/hackatanay/wall.png"
        for edge in candidate_edges:
            if edge == door_edge:
                self.door = Entity(
                    model='cube',
                    color=color.brown,
                    collider='box',
                    position=edge['pos'],
                    scale=edge['scale'],
                    name='door'
                )

                self.door_direction = edge['direction']
            else:
                wall = Entity(
                    model='cube',
                    color=color.gray,
                    collider='box',
                    position=edge['pos'],
                    scale=edge['scale']
                )
                wall.texture = tex
                self.wall_tiles.append(wall)

    def open_door(self):
        if self.door and not self.door_open:
            destroy(self.door)
            self.door = None
            self.door_open = True
            return True
        return False

    def generate(self):
        self.generate_rooms()
        self.generate_floor()
        self.generate_walls()
        self.place_teleporter()

    def place_teleporter(self):
        if self.teleporter:
            destroy(self.teleporter)
        self.teleporter = None

        if self.floor_tiles:
            last_tile = self.floor_tiles[-1]
            self.teleporter = Entity(
                model='cube',
                color=color.azure,
                scale=(0.5, 0.5, 0.5),
                position=last_tile.position + Vec3(0, 0.3, 0),
                collider='box',
                name='teleporter'
            )


    def get_spawn_floor_tile(self):
        return self.floor_tiles[0] if self.floor_tiles else None

    def set_trap(self, corridor_tiles):
        for tile in corridor_tiles:
            prob = random.randint(1, 28)
            if prob == 1 or prob == 2:
                trap = Entity(
                    position=tile.position + Vec3(0, 1, 0),
                    model='cube',
                    color=color.hsv(0, 0, 1, .05),
                    scale=(0.5, 0.25, 0.5),
                    collider='box',
                    active=True,
                    damage=7, )

                self.traps.append(trap)