from ursina import *
from ursina import time


class AnimatedTool(Entity):
    def __init__(self,image):
        super().__init__(
            parent=camera.ui,
            model='quad',
            texture=image,
            tileset_size=(6, 1),
            scale=(1, 0.5),
            position=(0.22, -0.18),
            rotation_z=25,
            visible=True
        )
        self.tool='sword'
        self.frame = 0
        self.max_frames = 6
        self.fps = 6
        self.playing = False
        self.timer = 0

    def play(self):
        self.frame = 0
        self.playing = True
        self.timer = 0

    def update(self):
        if self.playing:
            self.timer += time.dt
            if self.timer > 1 / self.fps:
                self.timer = 0
                self.frame += 1
                if self.frame >= self.max_frames:
                    self.playing = False
                    self.frame = 0
                self.set_frame(self.frame)

    def set_frame(self, index):
        x = index / self.max_frames
        self.texture_offset = (x, 0)

class Player(Entity):
    def __init__(self, position=(0, 1, 0)):
        super().__init__()
        self.controller = Entity(
            position=position,
            model='cube',
            scale=(0.25, 0.25, 0.25),
            collider='box',
            visible=False,
            player=True
        )
        self.healthbar_back = Entity(
            model='quad',
            parent=camera.ui,
            scale=(0.51,0.0725),
            color=color.black,
            position=(-0.5,0.4)
        )
        self.healthbar_front = Entity(
            model='quad',
            parent=camera.ui,
            scale=(0.5, 0.0625),
            color=color.green,
            position=(-0.5,0.4)
        )
        self.tool = AnimatedTool(image='assets/hackatanay/sword_animation.png')


        camera.parent = self.controller
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)

        mouse.locked = False
        mouse.visible = True

        self.speed = 2
        self.turn_speed = 45
        self.health = 20
        self.attack_range = 1.5
        self.attack_cooldown = 0.5
        self._last_attack_time = 0

    def update(self):
        dt = time.dt

        speed = self.speed * dt
        direction = Vec3(0, 0, 0)

        if held_keys['right arrow']:
            self.controller.rotation_y += self.turn_speed * dt
        if held_keys['left arrow']:
            self.controller.rotation_y -= self.turn_speed * dt

        if held_keys['up arrow']:
            direction += self.controller.forward
        if held_keys['down arrow']:
            direction -= self.controller.forward
        if held_keys['space']:
            if self.tool.tool=='defuse':
                self.disarm()
            if self.tool.tool=='sword' and time.time() - self._last_attack_time > self.attack_cooldown:
                self.attack()
        if held_keys['1']:
            self.tool.tool='sword'
            self.tool.texture='assets/hackatanay/sword_animation.png'
        if held_keys['2']:
            self.tool.tool='defuser'
            self.tool.texture='assets/hackatanay/disarmer.png'

        direction += self.controller.right * (held_keys['d'] - held_keys['a'])
        direction += self.controller.forward * (held_keys['w'] - held_keys['s'])

        if direction != Vec3(0, 0, 0):
            direction = direction.normalized() * speed
            original_pos = self.controller.position
            self.controller.position += direction
            if self.controller.intersects().hit:
                if hasattr(self.controller.intersects().entity,'active'):
                    if self.tool.tool!='defuser':
                        self.health-=7
                    else:
                        self.tool.play()
                    destroy(self.controller.intersects().entity)
                self.controller.position = original_pos

        self.controller.y = max(self.controller.y, 0.5)
        self.position = self.controller.position
        self.tool.update()

        h_offset=-0.75+self.health/80
        self.healthbar_front.scale = (self.health/40,0.0625)
        self.healthbar_front.position = (h_offset,0.4)

    def attack(self):
        self._last_attack_time = time.time()

        hit_info = raycast(
            origin=self.controller.world_position,
            direction=self.controller.forward,
            distance=self.attack_range,
            ignore=(self.controller,)
        )

        if hit_info.hit and hasattr(hit_info.entity, 'health'):
            self.tool.play()
            hit_info.entity.health -= 1
            print(f"Enemy hit! Health left: {hit_info.entity.health}")

    def disarm(self):
        self._last_attack_time = time.time()

        hit_info = raycast(
            origin=self.controller.position,
            direction=self.controller.forward,
            distance=2,
            ignore=(self.controller,)
        )
        if hit_info.hit and hasattr(hit_info.entity, 'active'):
            self.tool.play()
            destroy(hit_info.entity)
            print('Trap Disarmed')