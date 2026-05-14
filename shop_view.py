import arcade
import os

ASSETS = "assets"
SHOP_ASSETS = os.path.join(ASSETS, "buy")


def get_shop_asset(*parts):
    return os.path.join(SHOP_ASSETS, *parts)


class ShopItem(arcade.Sprite):
    def __init__(self, name, x, y, price, asset):
        super().__init__()
        self.name = name
        self.price = price
        self.center_x = x
        self.center_y = y

        try:
            self.texture = arcade.load_texture(get_shop_asset(asset))
        except:
            self.texture = arcade.make_soft_square_texture(32, arcade.color.WHITE, 255, 255)

        self.scale = 1.5


class Merchant(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(get_shop_asset("dealer"))
        except:
            self.texture = arcade.make_soft_square_texture(64, arcade.color.WHITE, 255, 255)

        self.center_x = x
        self.center_y = y
        self.scale = 1.5


class ShopView(arcade.View):
    def __init__(self, player):
        super().__init__()

        self.player = player
        self.shop_open = False

        self.merchant = Merchant(500, 250)

        self.shop_items = arcade.SpriteList()
        self.shop_items.append(ShopItem("legs", 350, 300, 5, "leg"))
        self.shop_items.append(ShopItem("arms", 450, 300, 5, "hands"))
        self.shop_items.append(ShopItem("mouth", 550, 300, 5, "mouth"))
        self.shop_items.append(ShopItem("ear", 650, 300, 5, "ear"))

    def on_draw(self):
        self.clear()

        self.shop_items.draw()
        self.merchant.draw()
        self.player.draw()

        arcade.draw_text(
            "E - открыть магазин",
            50,
            700,
            arcade.color.WHITE,
            16
        )

        if self.shop_open:
            arcade.draw_rectangle_filled(512, 384, 600, 300, (0, 0, 0, 180))
            arcade.draw_text(
                "SHOP",
                512,
                520,
                arcade.color.WHITE,
                24,
                anchor_x="center"
            )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.E:
            self.shop_open = not self.shop_open

        if key == arcade.key.R:
            # возврат в игру (ВАЖНО: GameView не трогаем)
            from main import GameView
            game = GameView()
            game.player = self.player
            self.window.show_view(game)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.shop_open:
            return

        for item in self.shop_items:
            if item.collides_with_point((x, y)):
                if self.player.coins >= item.price:
                    self.player.coins -= item.price

                    if item.name == "legs":
                        self.player.speed_mult = 1.5
                    elif item.name == "arms":
                        self.player.damage = 2
                    elif item.name == "mouth":
                        self.player.has_mouth = True
                    elif item.name == "ear":
                        self.player.has_ear = True

                    item.kill()