import arcade
import os
import random
import math

try:
    import noise
except ImportError:
    noise = None

WIDTH = 1024
HEIGHT = 768
TILE_SIZE = 64
GRAVITY = 0.8
JUMP_SPEED = 18
PLAYER_MAX_HEALTH = 4

ASSETS = "assets"

def get_asset(*parts):
    return os.path.join(ASSETS, *parts)

def load_animation(path, frame_width, frame_height, frame_count):
    textures = []
    try:
        sheet = arcade.load_texture(path)
        for i in range(frame_count):
            x = i * frame_width
            y = 0
            tex = sheet.crop(x, y, frame_width, frame_height)
            textures.append(tex)
        print(f"✓ Анимация загружена: {path} ({frame_count} кадров)")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {path}: {e}")
        textures = [arcade.make_soft_square_texture(frame_width, arcade.color.BLUE, 255, 255)]
    return textures

class SimpleRect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, px, py):
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

#ИГРОК
class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.state = "IDLE"
        self.facing_right = True
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.coins = 0
        self.speed = 5
        self.attack_damage = 1
        self.can_speak = False
        self.can_hear = False
        self.invincible_timer = 0.0
        self.attack_timer = 0.0

        base = ["player"]
        self._idle_orig = load_animation(get_asset(*base, "idle.png"), 128, 128, 6)
        self._run_orig   = load_animation(get_asset(*base, "run.png"), 128, 128, 8)
        self._jump_orig  = load_animation(get_asset(*base, "jump.png"), 128, 128, 12)
        self._attack_orig= load_animation(get_asset(*base, "attack.png"), 128, 128, 6)
        self._dead_orig  = load_animation(get_asset(*base, "dead.png"), 128, 128, 3)

        self.idle_textures = self._idle_orig
        self.run_textures = self._run_orig
        self.jump_textures = self._jump_orig
        self.attack_textures = self._attack_orig
        self.dead_textures = self._dead_orig

        self.current_texture_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.1
        self.texture = self.idle_textures[0]
        self.scale = 0.5

        self.jump_sounds = self._load_sounds(["jump1.wav", "jump2.wav", "jump3.wav"], 0.3)
        self.attack_sounds = self._load_sounds(["attack1.wav", "attack2.wav", "attack3.wav"], 0.3)
        self.damage_sounds = self._load_sounds(["damaged1.wav", "damaged2.wav", "damaged3.wav"], 0.3)

    def _load_sounds(self, filenames, volume):
        sounds = []
        for fname in filenames:
            try:
                snd = arcade.load_sound(get_asset("music", fname))
                snd.volume = volume
                sounds.append(snd)
            except:
                pass
        return sounds

    def _update_orientation(self):
        if self.facing_right:
            self.idle_textures = self._idle_orig
            self.run_textures   = self._run_orig
            self.jump_textures  = self._jump_orig
            self.attack_textures= self._attack_orig
            self.dead_textures  = self._dead_orig
        else:
            self.idle_textures = [tex.flip_horizontally() for tex in self._idle_orig]
            self.run_textures   = [tex.flip_horizontally() for tex in self._run_orig]
            self.jump_textures  = [tex.flip_horizontally() for tex in self._jump_orig]
            self.attack_textures= [tex.flip_horizontally() for tex in self._attack_orig]
            self.dead_textures  = [tex.flip_horizontally() for tex in self._dead_orig]

    def update_animation(self, delta_time):
        self.animation_timer += delta_time
        if self.state == "DEAD":
            textures = self.dead_textures
            speed = self.animation_speed
        elif self.state == "ATTACKING":
            textures = self.attack_textures
            speed = self.animation_speed * 2
        elif self.state == "JUMPING":
            textures = self.jump_textures
            speed = self.animation_speed
        elif abs(self.change_x) > 0.5:
            self.state = "RUNNING"
            textures = self.run_textures
            speed = self.animation_speed
        else:
            if self.state != "ATTACKING":
                self.state = "IDLE"
            textures = self.idle_textures
            speed = self.animation_speed * 0.5

        if textures and self.animation_timer >= speed:
            self.animation_timer = 0
            self.current_texture_index += 1
            if self.state == "DEAD" and self.current_texture_index >= len(textures):
                self.current_texture_index = len(textures) - 1
            else:
                self.current_texture_index %= len(textures)
            self.texture = textures[self.current_texture_index]

    def attack(self):
        if self.state not in ("DEAD", "ATTACKING"):
            self.state = "ATTACKING"
            self.current_texture_index = 0
            self.attack_timer = 0.5
            if self.can_speak and self.can_hear and self.attack_sounds:
                arcade.play_sound(random.choice(self.attack_sounds))
            return True
        return False

    def take_damage(self, damage):
        if self.invincible_timer <= 0 and self.state != "DEAD":
            self.health -= damage
            self.invincible_timer = 1.5
            if self.can_speak and self.can_hear and self.damage_sounds:
                arcade.play_sound(random.choice(self.damage_sounds))
            if self.health <= 0:
                self.health = 0
                self.state = "DEAD"
                self.current_texture_index = 0
                self.change_x = 0
            return True
        return False

    def update(self, delta_time):
        if self.state == "DEAD":
            self.update_animation(delta_time)
            return

        if self.attack_timer > 0:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0:
                self.state = "IDLE"

        if self.invincible_timer > 0:
            self.invincible_timer -= delta_time

        if self.change_x > 0:
            self.facing_right = True
        elif self.change_x < 0:
            self.facing_right = False

        self._update_orientation()
        self.update_animation(delta_time)

        self.alpha = 255
        if self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0:
            self.alpha = 128

#ВРАГ
class Enemy(arcade.Sprite):
    def __init__(self, x, y, slime_type):
        super().__init__()
        self.damage = 1
        self.health = 3
        self.attack_cooldown = 0.0

        filename = f"{slime_type}_Jump.png"
        self.textures = load_animation(get_asset("enemy", filename), 32, 32, 3)
        self.current_texture_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.15
        self.texture = self.textures[0]
        self.center_x = x
        self.center_y = y
        self.scale = 1.0

    def update(self, delta_time, player):
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_texture_index = (self.current_texture_index + 1) % len(self.textures)
            self.texture = self.textures[self.current_texture_index]

        self.change_y -= GRAVITY

        if self.attack_cooldown <= 0:
            if arcade.check_for_collision(self, player):
                player.take_damage(self.damage)
                self.attack_cooldown = 1.0
        else:
            self.attack_cooldown -= delta_time

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False

#ПРЕДМЕТЫ
class Coin(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(get_asset("Icons", "Icon_Coin_1.png"))
        except:
            self.texture = arcade.make_soft_circle_texture(8, arcade.color.GOLD, 255, 255)
        self.center_x = x
        self.center_y = y
        self.scale = 2.0
        self.value = 1
        self.animation_angle = 0

    def update(self, delta_time=0):
        self.animation_angle += 5
        self.angle = math.sin(math.radians(self.animation_angle)) * 10

class HealthPickup(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(get_asset("Icons", "Icon_Point_1.png"))
        except:
            self.texture = arcade.make_soft_square_texture(8, arcade.color.RED, 255, 255)
        self.center_x = x
        self.center_y = y
        self.scale = 2.0
        self.heal_amount = 1

#ТОРГОВЕЦ
class Merchant(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(get_asset("buy", "dealer.png"))
        except:
            self.texture = arcade.make_soft_square_texture(64, arcade.color.YELLOW, 255, 255)
        self.center_x = x
        self.center_y = y
        self.scale = 1.0

class Tent(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(get_asset("buy", "merchants_tent.png"))
        except:
            self.texture = arcade.make_soft_square_texture(128, 96, arcade.color.BROWN, 255, 255)
        self.center_x = x
        self.center_y = y
        self.scale = 1.0

#ОСНОВНОЙ ВИД
class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.camera = None
        self.player = None
        self.player_list = None
        self.background_list = None
        self.wall_list = None
        self.enemy_list = None
        self.coin_list = None
        self.item_list = None
        self.physics_engine = None
        self.heart_full = None
        self.heart_empty = None
        self.game_over = False
        self.victory = False

        self.merchant = None
        self.tent = None
        self.shop_sprites = None
        self.shop_open = False
        self.shop_buttons = {}
        self.hands_icon = None
        self.legs_icon = None
        self.mouth_icon = None
        self.ear_icon = None
        self.coin_icon = None

        self.coin_sound = self._load_sound("money.wav", 0.3)
        self.heal_sounds = self._load_sounds(["healed1.wav", "healed2.wav", "healed3.wav"], 0.3)

    def _load_sound(self, filename, volume):
        try:
            snd = arcade.load_sound(get_asset("music", filename))
            snd.volume = volume
            return snd
        except:
            return None

    def _load_sounds(self, filenames, volume):
        sounds = []
        for fname in filenames:
            snd = self._load_sound(fname, volume)
            if snd:
                sounds.append(snd)
        return sounds

    def setup(self):
        self.game_over = False
        self.victory = False
        self.camera = arcade.Camera2D()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.enemy_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList(use_spatial_hash=True)
        self.item_list = arcade.SpriteList(use_spatial_hash=True)
        self.player_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.shop_sprites = arcade.SpriteList()

        #ФОН
        try:
            bg_tex = arcade.load_texture(get_asset("Backgrounds", "Background_Cave", "background_Cave.png"))
            bg_sprite = arcade.Sprite(bg_tex)
            bg_sprite.center_x = WIDTH / 2
            bg_sprite.center_y = HEIGHT / 2
            bg_sprite.width = WIDTH
            bg_sprite.height = HEIGHT
            self.background_list.append(bg_sprite)
        except:
            pass

        #Сердца
        try:
            self.heart_full = arcade.load_texture(get_asset("Icons", "Icon_Heart_1.png"))
        except:
            self.heart_full = None
        try:
            self.heart_empty = arcade.load_texture(get_asset("Icons", "Icon_Heart_2.png"))
        except:
            self.heart_empty = None

        #Товары
        try:
            self.hands_icon = arcade.load_texture(get_asset("buy", "hands.png"))
        except:
            self.hands_icon = None
        try:
            self.legs_icon = arcade.load_texture(get_asset("buy", "leg.png"))
        except:
            self.legs_icon = None
        try:
            self.mouth_icon = arcade.load_texture(get_asset("buy", "mouth.png"))
        except:
            self.mouth_icon = None
        try:
            self.ear_icon = arcade.load_texture(get_asset("buy", "ear.png"))
        except:
            self.ear_icon = None
        try:
            self.coin_icon = arcade.load_texture(get_asset("Icons", "Icon_Coin_1.png"))
        except:
            self.coin_icon = None

        self.player = Player()
        self.player.center_x = 200
        self.player.center_y = 300
        self.player_list.append(self.player)

        self.generate_level()

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, walls=self.wall_list, gravity_constant=GRAVITY
        )

    def generate_level(self):
        self.wall_list.clear()
        self.enemy_list.clear()
        self.coin_list.clear()
        self.item_list.clear()

        #Зона торговца
        for x in range(-800 + TILE_SIZE//2, 0, TILE_SIZE):
            try:
                tex = arcade.load_texture(get_asset("buy", "Dirt-Grass.png"))
                tile = arcade.Sprite(tex, scale=1)
            except:
                tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.DARK_BROWN)
            tile.center_x = x
            tile.center_y = TILE_SIZE // 2
            self.wall_list.append(tile)

        merchant_x = -600 + TILE_SIZE//2
        self.tent = Tent(merchant_x, TILE_SIZE + 48)
        self.merchant = Merchant(merchant_x, TILE_SIZE + 48)
        self.shop_sprites.append(self.tent)
        self.shop_sprites.append(self.merchant)

        wall_height = 10
        for yy in range(wall_height):
            tile_left = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.WHITE)
            tile_left.center_x = -800 + TILE_SIZE // 2
            tile_left.center_y = yy * TILE_SIZE + TILE_SIZE // 2
            tile_left.visible = False
            self.wall_list.append(tile_left)

        #Переходная зона (0‑200)
        for x in range(TILE_SIZE//2, 200, TILE_SIZE):
            try:
                tex = arcade.load_texture(get_asset("Tile Sets", "Dirt.png"))
                tile = arcade.Sprite(tex, scale=1)
            except:
                tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.DARK_BROWN)
            tile.center_x = x
            tile.center_y = TILE_SIZE // 2
            self.wall_list.append(tile)

        #Основной уровень (200‑3000)
        floor_tops = []
        x = 200
        gap_counter = 0
        while x < 3000:
            if gap_counter <= 0 and random.random() < 0.1:
                gap_counter = random.randint(2, 4)
            if gap_counter > 0:
                gap_counter -= 1
                x += TILE_SIZE
                continue

            try:
                tex = arcade.load_texture(get_asset("Tile Sets", "Dirt.png"))
                tile = arcade.Sprite(tex, scale=1)
            except:
                tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.DARK_BROWN)
            tile.center_x = x
            tile.center_y = TILE_SIZE // 2
            self.wall_list.append(tile)
            floor_tops.append((x, TILE_SIZE))
            x += TILE_SIZE

        platforms_info = []
        x = 200
        last_y = None
        while x < 2800:
            if noise:
                n = noise.pnoise1(x * 0.01, octaves=3)
                y_base = 150 + (n + 1) * 100
            else:
                y_base = random.randint(150, 350)

            if last_y is not None:
                y_base = max(last_y - 120, min(last_y + 120, y_base))
            last_y = y_base

            length = random.randint(3, 6)
            for i in range(length):
                try:
                    tex = arcade.load_texture(get_asset("Tile Sets", "Stone-Bricks.png"))
                    tile = arcade.Sprite(tex, scale=1)
                except:
                    tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.GRAY)
                tile.center_x = x + i * TILE_SIZE + TILE_SIZE // 2
                tile.center_y = y_base + TILE_SIZE // 2
                self.wall_list.append(tile)
            platforms_info.append((x, y_base, length))
            x += length * TILE_SIZE + random.randint(1, 2) * TILE_SIZE

        enemy_types = ["BlueSlime", "greenSlime", "RedSlime"]
        for _ in range(4):
            if floor_tops:
                fx, top = random.choice(floor_tops)
                ex = fx
                ey = top + 32
                self.enemy_list.append(Enemy(ex, ey, random.choice(enemy_types)))

        for px, py, plen in platforms_info:
            if random.random() < 0.7:
                ex = px + random.randint(1, plen-1) * TILE_SIZE + TILE_SIZE // 2
                ey = py + TILE_SIZE + 32
                self.enemy_list.append(Enemy(ex, ey, random.choice(enemy_types)))

        for _ in range(45):
            if random.random() < 0.6 and floor_tops:
                fx, top = random.choice(floor_tops)
                cx = fx
                cy = top + 24
            elif platforms_info:
                px, py, plen = random.choice(platforms_info)
                cx = px + random.randint(1, plen-1) * TILE_SIZE + TILE_SIZE // 2
                cy = py + TILE_SIZE + 24
            else:
                continue
            self.coin_list.append(Coin(cx, cy))

        for _ in range(5):
            if platforms_info:
                px, py, plen = random.choice(platforms_info)
                cx = px + random.randint(1, plen-1) * TILE_SIZE + TILE_SIZE // 2
                cy = py + TILE_SIZE + 24
                self.item_list.append(HealthPickup(cx, cy))

        for yy in range(wall_height):
            tile_right = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.WHITE)
            tile_right.center_x = 3000 - TILE_SIZE // 2
            tile_right.center_y = yy * TILE_SIZE + TILE_SIZE // 2
            tile_right.visible = False
            self.wall_list.append(tile_right)

        #Монетки в зоне торговца
        for _ in range(5):
            cx = random.randint(-750, -50)
            cy = TILE_SIZE + 20
            self.coin_list.append(Coin(cx, cy))

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        # Фон
        self.window.default_camera.use()
        self.background_list.draw()
        # Мир
        self.camera.use()
        self.shop_sprites.draw()
        self.wall_list.draw()
        self.coin_list.draw()
        self.item_list.draw()
        self.enemy_list.draw()
        self.player_list.draw()
        #Подсказка "E"
        if self.merchant and not self.shop_open and not self.victory:
            dist = math.hypot(self.player.center_x - self.merchant.center_x,
                              self.player.center_y - self.merchant.center_y)
            if dist < 80:
                arcade.Text("Нажми E", self.merchant.center_x, self.merchant.center_y + 40,
                            arcade.color.WHITE, 14, anchor_x="center").draw()
        # UI
        self.window.default_camera.use()
        self.draw_ui()
        if self.game_over:
            self.draw_game_over()
        elif self.victory:
            self.draw_victory()
        if self.shop_open:
            self.draw_shop_gui()

    def draw_ui(self):
        heart_x = 40
        heart_y = HEIGHT - 50
        heart_size = 32
        for i in range(PLAYER_MAX_HEALTH):
            tex = self.heart_full if i < self.player.health else self.heart_empty
            if tex:
                arcade.draw_texture_rect(tex, arcade.rect.XYWH(heart_x + i * (heart_size + 5), heart_y, heart_size, heart_size))
        arcade.Text(f"Монеты: {self.player.coins}", 40, HEIGHT - 90, arcade.color.WHITE, 20).draw()
        arcade.Text("WASD - движение | SPACE - прыжок | ЛКМ - атака", 20, 20, arcade.color.WHITE, 14).draw()

    def draw_game_over(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(WIDTH//2, HEIGHT//2, 400, 200), (0, 0, 0, 200))
        arcade.Text("GAME OVER", WIDTH//2, HEIGHT//2 + 40, arcade.color.RED, 36,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text(f"Собрано монет: {self.player.coins}", WIDTH//2, HEIGHT//2,
                    arcade.color.WHITE, 20, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Нажми R для перезапуска", WIDTH//2, HEIGHT//2 - 40,
                    arcade.color.WHITE, 16, anchor_x="center", anchor_y="center").draw()

    def draw_victory(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(WIDTH//2, HEIGHT//2, 400, 200), (0, 0, 0, 200))
        arcade.Text("VICTORY", WIDTH//2, HEIGHT//2 + 40, arcade.color.GREEN, 36,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text(f"Все враги повержены!", WIDTH//2, HEIGHT//2,
                    arcade.color.WHITE, 20, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Нажми R для перезапуска", WIDTH//2, HEIGHT//2 - 40,
                    arcade.color.WHITE, 16, anchor_x="center", anchor_y="center").draw()

    def draw_shop_gui(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(WIDTH/2, HEIGHT/2, 400, 300), (0, 0, 0, 200))
        arcade.Text("Торговец", WIDTH/2, HEIGHT/2 + 130, arcade.color.WHITE, 24, anchor_x="center", anchor_y="center").draw()

        btn_hands = SimpleRect(WIDTH/2 - 150, HEIGHT/2 + 40, 120, 40)
        arcade.draw_rect_filled(arcade.rect.XYWH(btn_hands.x + btn_hands.width/2, btn_hands.y + btn_hands.height/2, btn_hands.width, btn_hands.height), arcade.color.DARK_GREEN)
        arcade.Text("Руки 5", WIDTH/2 - 90, HEIGHT/2 + 60, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center").draw()
        if self.hands_icon:
            arcade.draw_texture_rect(self.hands_icon, arcade.rect.XYWH(WIDTH/2 - 140, HEIGHT/2 + 45, 20, 20))
        self.shop_buttons['hands'] = btn_hands

        btn_legs = SimpleRect(WIDTH/2 + 30, HEIGHT/2 + 40, 120, 40)
        arcade.draw_rect_filled(arcade.rect.XYWH(btn_legs.x + btn_legs.width/2, btn_legs.y + btn_legs.height/2, btn_legs.width, btn_legs.height), arcade.color.DARK_GREEN)
        arcade.Text("Ноги 5", WIDTH/2 + 90, HEIGHT/2 + 60, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center").draw()
        if self.legs_icon:
            arcade.draw_texture_rect(self.legs_icon, arcade.rect.XYWH(WIDTH/2 + 40, HEIGHT/2 + 45, 20, 20))
        self.shop_buttons['legs'] = btn_legs

        btn_mouth = SimpleRect(WIDTH/2 - 150, HEIGHT/2 - 10, 120, 40)
        arcade.draw_rect_filled(arcade.rect.XYWH(btn_mouth.x + btn_mouth.width/2, btn_mouth.y + btn_mouth.height/2, btn_mouth.width, btn_mouth.height), arcade.color.DARK_GREEN)
        arcade.Text("Рот 5", WIDTH/2 - 90, HEIGHT/2 + 10, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center").draw()
        if self.mouth_icon:
            arcade.draw_texture_rect(self.mouth_icon, arcade.rect.XYWH(WIDTH/2 - 140, HEIGHT/2 - 5, 20, 20))
        self.shop_buttons['mouth'] = btn_mouth

        btn_ear = SimpleRect(WIDTH/2 + 30, HEIGHT/2 - 10, 120, 40)
        arcade.draw_rect_filled(arcade.rect.XYWH(btn_ear.x + btn_ear.width/2, btn_ear.y + btn_ear.height/2, btn_ear.width, btn_ear.height), arcade.color.DARK_GREEN)
        arcade.Text("Ухо 5", WIDTH/2 + 90, HEIGHT/2 + 10, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center").draw()
        if self.ear_icon:
            arcade.draw_texture_rect(self.ear_icon, arcade.rect.XYWH(WIDTH/2 + 40, HEIGHT/2 - 5, 20, 20))
        self.shop_buttons['ear'] = btn_ear

        btn_exit = SimpleRect(WIDTH/2 - 50, HEIGHT/2 - 60, 100, 40)
        arcade.draw_rect_filled(arcade.rect.XYWH(btn_exit.x + btn_exit.width/2, btn_exit.y + btn_exit.height/2, btn_exit.width, btn_exit.height), arcade.color.DARK_RED)
        arcade.Text("Выход", WIDTH/2, HEIGHT/2 - 40, arcade.color.WHITE, 16, anchor_x="center", anchor_y="center").draw()
        self.shop_buttons['exit'] = btn_exit

        arcade.Text(f"Ваши монеты: {self.player.coins}", WIDTH/2, HEIGHT/2 - 100, arcade.color.GOLD, 14, anchor_x="center").draw()

    def on_update(self, delta_time):
        if self.game_over or self.shop_open or self.victory:
            return

        if self.player.state == "DEAD":
            self.player.update(delta_time)
            if self.player.current_texture_index == len(self.player.dead_textures) - 1:
                self.game_over = True
            return

        self.physics_engine.update()
        self.player.update(delta_time)
        self.camera.position = (self.player.center_x, HEIGHT // 2)

        #Враги и атака
        for enemy in self.enemy_list:
            enemy.update(delta_time, self.player)
            if self.player.state == "ATTACKING" and 0.2 < self.player.attack_timer < 0.4:
                attack_width = 50
                attack_height = 40
                if self.player.facing_right:
                    attack_x = self.player.center_x + 30
                else:
                    attack_x = self.player.center_x - 30
                # Прямая проверка столкновений без Rect
                if (abs(attack_x - enemy.center_x) < attack_width/2 + enemy.width/2 and
                    abs(self.player.center_y - enemy.center_y) < attack_height/2 + enemy.height/2):
                    if enemy.take_damage(self.player.attack_damage):
                        self.coin_list.append(Coin(enemy.center_x, enemy.center_y))
                        print("Враг получил урон!")

        #Проверка победы
        if len(self.enemy_list) == 0:
            self.victory = True
            return

        # Монетки
        self.coin_list.update()
        coins_hit = arcade.check_for_collision_with_list(self.player, self.coin_list)
        for coin in coins_hit:
            self.player.coins += coin.value
            if self.player.can_hear and self.coin_sound:
                arcade.play_sound(self.coin_sound)
            coin.kill()

        # Хилки
        self.item_list.update()
        items_hit = arcade.check_for_collision_with_list(self.player, self.item_list)
        for item in items_hit:
            if isinstance(item, HealthPickup):
                self.player.health = min(self.player.max_health, self.player.health + item.heal_amount)
                if self.player.can_hear and self.heal_sounds:
                    arcade.play_sound(random.choice(self.heal_sounds))
            item.kill()

        if self.player.center_y < -100:
            self.player.health = 0
            self.player.state = "DEAD"

    def on_key_press(self, key, modifiers):
        if self.game_over or self.victory:
            if key == arcade.key.R:
                self.setup()
            return

        if self.shop_open:
            if key == arcade.key.ESCAPE or key == arcade.key.E:
                self.shop_open = False
            return

        if self.player.state == "DEAD":
            return

        if key == arcade.key.A:
            self.player.change_x = -self.player.speed
        elif key == arcade.key.D:
            self.player.change_x = self.player.speed
        elif key in (arcade.key.W, arcade.key.SPACE):
            if self.physics_engine and self.physics_engine.can_jump():
                self.player.change_y = JUMP_SPEED
                if self.player.can_speak and self.player.can_hear and self.player.jump_sounds:
                    arcade.play_sound(random.choice(self.player.jump_sounds))
        elif key == arcade.key.E:
            if self.merchant:
                dist = math.hypot(self.player.center_x - self.merchant.center_x,
                                  self.player.center_y - self.merchant.center_y)
                if dist < 80:
                    self.shop_open = True

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.A, arcade.key.D) and self.player:
            self.player.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        if self.shop_open and button == arcade.MOUSE_BUTTON_LEFT:
            for btn_name, rect in self.shop_buttons.items():
                if rect.contains(x, y):
                    if btn_name == 'hands' and self.player.coins >= 5:
                        self.player.coins -= 5
                        self.player.attack_damage += 1
                    elif btn_name == 'legs' and self.player.coins >= 5:
                        self.player.coins -= 5
                        self.player.speed += 2
                    elif btn_name == 'mouth' and self.player.coins >= 5:
                        self.player.coins -= 5
                        self.player.can_speak = True
                    elif btn_name == 'ear' and self.player.coins >= 5:
                        self.player.coins -= 5
                        self.player.can_hear = True
                    elif btn_name == 'exit':
                        self.shop_open = False
                    break
        elif not self.game_over and not self.victory and self.player.state != "DEAD":
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.player.attack()

def main():
    window = arcade.Window(WIDTH, HEIGHT, "Артефакт Подземелий", resizable=True)
    game = GameView()
    game.setup()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()