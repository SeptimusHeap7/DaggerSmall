from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from dungeon import Dungeon
from player import Player
from enemy import Enemy
import math
app = Ursina()
enemies = []
teleport_offset = Vec3(-100, 0, 0)
game_started = False  # Flag to check if the game has started

# Title Screen Setup
title_screen = Entity(parent=camera.ui)

title_text = Text(
    parent=title_screen,
    font='assets/daggerfall.ttf',
    text='DaggerSmall',
    origin=(0, 0),
    scale=2,
    position=(0, 0.2),
    color=color.white

)

t = Text(
    parent=title_screen,
    font='assets/daggerfall.ttf',
    text='Try to get as far as you can! Watch out for traps and enemies.\n \nGet to the blue portal to get to the next dungeon. 1 for knife, 2 for disarmer, \n\nhold disarmer whilst walking through traps to diffuse,\n\n press e to go through portal',
    origin=(0,0),
    scale=0.5,
    position=(0,-0.3),
    color=color.white
)

def start_game():
    global dungeon, player, game_started
    game_started = True
    title_screen.disable()
    start_button.disable()

    # Generate first dungeon
    dungeon = Dungeon()
    dungeon.generate()
    dungeon.set_trap(dungeon.corridor_tiles)

    # Spawn player
    spawn_tile = dungeon.get_spawn_floor_tile()
    player_start_pos = (spawn_tile.x, 1, spawn_tile.z) if spawn_tile else (0, 1, 0)
    player = Player(position=player_start_pos)

    # Destroy the default cursor


    # Create a custom white crosshair
    crosshair = Entity(
        parent=camera.ui,
        model='quad',
        color=color.white,
        scale=0.005,
        position=(0, 0)
    )

    spawn_enemies_for_all_rooms(dungeon)

start_button = Button(
    parent=title_screen,
    text='Start Game',
    color=color.azure,
    scale=(0.5, 0.1),
    position=(0, -0.1),
    on_click=start_game
)

# Minimap setup
minimap_camera = EditorCamera(enabled=False)
minimap_camera.orthographic = True
minimap_camera.fov = 20
minimap_camera.rotation_x = 90
minimap_camera.y = 30

minimap_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(0, 0, 0, 120),
    scale=(0.3, 0.3),
    position=(-0.7, 0.4),
    enabled=False
)

minimap_icon = Entity(
    parent=minimap_bg,
    model='circle',
    color=color.red,
    scale=0.02,
    position=(0, 0),
    enabled=False
)

def input(key):
    if not game_started:
        return
    if key == 'm':
        toggle_minimap()
    if key == 'e':
        check_for_teleporter()

def check_for_teleporter():
    global dungeon
    player_pos = player.controller.position
    teleporter = dungeon.teleporter

    if teleporter and distance(player_pos, teleporter.position) < 2:
        print("Teleporter activated!")
        teleport_to_new_dungeon(dungeon)

def spawn_enemies_in_room(x, z, room_width, room_height, wall_tiles, floor_tiles, offset=Vec3(0,0,0)):
    center_x = x + room_width // 2
    center_z = z + room_height // 2
    base_pos = Vec3(center_x * dungeon.tile_size, 0, center_z * dungeon.tile_size) + offset
    offset_dist = 2

    positions = [
        base_pos + Vec3(0, 0, 0)
    ]

    for pos in positions:
        enemy = Enemy(position=pos, floor_tiles=floor_tiles, wall_tiles=wall_tiles, player=player)

        def safe_check(e=enemy, walls=wall_tiles):
            try:
                if e.collides_with_any_wall():
                    destroy(e)
                else:
                    enemies.append(e)
            except Exception as err:
                print("Error during enemy collision check:", err)
                destroy(e)

        invoke(safe_check, delay=1/60)

def spawn_enemies_for_all_rooms(dungeon_obj, offset=Vec3(0,0,0)):
    for room in dungeon_obj.rooms:
        x, z, w, h = room
        spawn_enemies_in_room(x, z, w, h, dungeon_obj.wall_tiles, dungeon_obj.floor_tiles, offset)

def teleport_to_new_dungeon(previous_dungeon):
    global dungeon, enemies

    # Destroy old dungeon entities
    for tile in previous_dungeon.floor_tiles + previous_dungeon.wall_tiles:
        destroy(tile)
    if previous_dungeon.teleporter:
        destroy(previous_dungeon.teleporter)

    previous_dungeon.floor_tiles.clear()
    previous_dungeon.wall_tiles.clear()
    previous_dungeon.teleporter = None

    # Destroy all old enemies
    for enemy in enemies:
        destroy(enemy)
    enemies.clear()

    # Generate new dungeon
    new_dungeon = Dungeon()
    new_dungeon.generate()






    # Calculate offset for new dungeon placement
    new_origin = player.controller.position + teleport_offset
    spawn_tile = new_dungeon.get_spawn_floor_tile()
    if spawn_tile:
        offset = new_origin - spawn_tile.position
    else:
        offset = new_origin

    # Apply offset to floor, walls, and teleporter
    for tile in new_dungeon.floor_tiles + new_dungeon.wall_tiles:
        tile.position += offset
    if new_dungeon.teleporter:
        new_dungeon.teleporter.position += offset

    # Move player to new spawn position (above floor)
    new_spawn = new_dungeon.get_spawn_floor_tile()
    if new_spawn:
        player.controller.position = new_spawn.position + Vec3(0, 1, 0)

    # Spawn enemies with the same offset so they appear in correct location
    spawn_enemies_for_all_rooms(new_dungeon, offset)
    new_dungeon.set_trap(new_dungeon.corridor_tiles)

    dungeon = new_dungeon

def toggle_minimap():
    minimap_camera.enabled = not minimap_camera.enabled
    minimap_bg.enabled = minimap_camera.enabled
    minimap_icon.enabled = minimap_camera.enabled

def update():
    if not game_started:
        return

    player.update()
    player.position += Vec3(1, 0, 0) * time.dt

    for enemy in enemies:
        if enemy and hasattr(enemy, 'update'):
            enemy.update()

    if minimap_camera.enabled:
        minimap_camera.x = player.controller.x
        minimap_camera.z = player.controller.z
        minimap_icon.position = (
            (player.controller.x - minimap_camera.x) / 20,
            (player.controller.z - minimap_camera.z) / 20
        )
    if player.health < 0:
        game_over = Entity(parent=camera.ui)
        end_text = Text(
            parent=game_over,
            font='assets/daggerfall.ttf',
            text='Game Over',
            origin=(0, 0),
            scale=2,
            position=(0, 0.2),
            color=color.white

        )




app.run()