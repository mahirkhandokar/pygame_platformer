"""
  2Example of Pymunk Physics Engine Platformer
  3"""
import math
from typing import Optional
import arcade
import os

SCREEN_TITLE = "The Legend of Rakesh"

# How big are our image tiles?
SPRITE_IMAGE_SIZE = 128

# Scale sprites up or down
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_TILES = 0.5

# Scaled sprite size for tiles
SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)

# Size of grid to show on screen, in number of tiles
SCREEN_GRID_WIDTH = 22
SCREEN_GRID_HEIGHT = 12

# Size of screen to show, in pixels
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

# --- Physics forces. Higher number, faster accelerating.

# Gravity
GRAVITY = 1600

# Damping - Amount of speed lost per second
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4

# Friction between objects
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Mass (defaults to 1)
PLAYER_MASS = 2.0

# Keep player from going too fast
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600

# Force applied while on the ground
PLAYER_MOVE_FORCE_ON_GROUND = 8000

# Force applied when moving left/right in the air
PLAYER_MOVE_FORCE_IN_AIR = 1200

# Strength of a jump
PLAYER_JUMP_IMPULSE = 1800

# Close enough to not-moving to have the animation go to idle.
DEAD_ZONE = 0.1

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

# How many pixels to move before we change the texture in the walking animation
DISTANCE_TO_CHANGE_TEXTURE = 20

# How much force to put on the bullet
BULLET_MOVE_FORCE = 9000

# Mass of the bullet
BULLET_MASS = 0.1

# Make bullet less affected by gravity
BULLET_GRAVITY = 300

LEFT_VIEWPORT_MARGIN = 200
RIGHT_VIEWPORT_MARGIN = 200
BOTTOM_VIEWPORT_MARGIN = 150
TOP_VIEWPORT_MARGIN = 100


class PlayerSprite(arcade.Sprite):
    """ Player Sprite """
    def __init__(self,
                 ladder_list: arcade.SpriteList,
                 hit_box_algorithm):
        """ Init """
        # Let parent initialize
        super().__init__()

        # Set our scale
        self.scale = SPRITE_SCALING_PLAYER

        # Images from Kenney.nl's Character pack
        # main_path = ":resources:images/animated_characters/female_adventurer/femaleAdventurer"
        #main_path = ":resources:images/animated_characters/female_person/femalePerson"
        main_path = ":resources:images/animated_characters/male_person/malePerson"
        # main_path = ":resources:images/animated_characters/male_adventurer/maleAdventurer"
        # main_path = ":resources:images/animated_characters/zombie/zombie"
        # main_path = ":resources:images/animated_characters/robot/robot"

        # Load textures for idle standing
        self.idle_texture_pair = arcade.load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = arcade.load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = arcade.load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = arcade.load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used.
        self.hit_box = self.texture.hit_box_points

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Index of our current texture
        self.cur_texture = 0

        # How far have we traveled horizontally since changing the texture
        self.x_odometer = 0
        self.y_odometer = 0

        self.ladder_list = ladder_list
        self.is_on_ladder = False

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle being moved by the pymunk engine """
        # Figure out if we need to face left or right
        if dx < -DEAD_ZONE and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif dx > DEAD_ZONE and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Are we on the ground?
        is_on_ground = physics_engine.is_on_ground(self)

        # Are we on a ladder?
        if len(arcade.check_for_collision_with_list(self, self.ladder_list)) > 0:
            if not self.is_on_ladder:
                self.is_on_ladder = True
                self.pymunk.gravity = (0, 0)
                self.pymunk.damping = 0.0001
                self.pymunk.max_vertical_velocity = PLAYER_MAX_HORIZONTAL_SPEED
        else:
            if self.is_on_ladder:
                self.pymunk.damping = 1.0
                self.pymunk.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
                self.is_on_ladder = False
                self.pymunk.gravity = None

        # Add to the odometer how far we've moved
        self.x_odometer += dx
        self.y_odometer += dy

        if self.is_on_ladder and not is_on_ground:
            # Have we moved far enough to change the texture?
            if abs(self.y_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

                # Reset the odometer
                self.y_odometer = 0

                # Advance the walking animation
                self.cur_texture += 1

            if self.cur_texture > 1:
                self.cur_texture = 0
            self.texture = self.climbing_textures[self.cur_texture]
            return

        # Jumping animation
        if not is_on_ground:
            if dy > DEAD_ZONE:
                self.texture = self.jump_texture_pair[self.character_face_direction]
                return
            elif dy < -DEAD_ZONE:
                self.texture = self.fall_texture_pair[self.character_face_direction]
                return

        # Idle animation
        if abs(dx) <= DEAD_ZONE:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Have we moved far enough to change the texture?
        if abs(self.x_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

            # Reset the odometer
            self.x_odometer = 0

            # Advance the walking animation
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]

class BulletSprite(arcade.SpriteSolidColor):
    """ Bullet Sprite """
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle when the sprite is moved by the physics engine. """
        # If the bullet falls below the screen, remove it
        if self.center_y < -100:
            self.remove_from_sprite_lists()

class TitleView(arcade.View):

    def __init__(self):
        super().__init__()
        my_map = arcade.tilemap.read_tmx("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/bg.tmx")
        self.grass = arcade.tilemap.process_layer(my_map, "Grass")
        self.sand = arcade.tilemap.process_layer(my_map, "Sand")
        self.snow = arcade.tilemap.process_layer(my_map, "Snow")
        self.haunted = arcade.tilemap.process_layer(my_map, "Haunted")
        self.city = arcade.tilemap.process_layer(my_map, "City")
        self.ladders = arcade.tilemap.process_layer(my_map, "Ladders")
        self.misc = arcade.tilemap.process_layer(my_map, "Misc.")
        self.platforms = arcade.tilemap.process_layer(my_map, "Platforms")

    def on_draw(self):
        arcade.start_render()
        self.grass.draw()
        self.sand.draw()
        self.snow.draw()
        self.haunted.draw()
        self.city.draw()
        self.platforms.draw()
        self.ladders.draw()
        self.misc.draw()
        arcade.draw_text("The Legend of Rakesh", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 175, arcade.color.BLACK, font_size=100,
                         anchor_x="center")
        arcade.draw_text("Play", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80, arcade.color.BLACK, font_size=30,
                         anchor_x="center")
        arcade.draw_text("Instructions", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40, arcade.color.BLACK, font_size=30,
                         anchor_x="center")
        arcade.draw_text("Levels", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 160, arcade.color.BLACK, font_size=30,
                         anchor_x="center")
        arcade.draw_text("Quit", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 280, arcade.color.BLACK, font_size=30,
                         anchor_x="center")

        # Rectangles for the buttons
        arcade.draw_lrtb_rectangle_outline(600, 800, 510, 460, arcade.color.BLACK, 3)
        arcade.draw_lrtb_rectangle_outline(600, 800, 390, 340, arcade.color.BLACK, 3)
        arcade.draw_lrtb_rectangle_outline(600, 800, 270, 220, arcade.color.BLACK, 3)
        arcade.draw_lrtb_rectangle_outline(600, 800, 150, 100, arcade.color.BLACK, 3)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if 600 < x < 800 and 460 < y < 510:
            game_view = GameWindow()
            game_view.setup(game_view.level)
            self.window.show_view(game_view)

        if 600 < x < 800 and 340 < y < 390:
            self.window.show_view(InstructionView())

        if 600 < x < 800 and 220 < y < 270:
            self.window.show_view(LevelView())

        if 600 < x < 800 and 100 < y < 150:
            os._exit(1)

class InstructionView(arcade.View):

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.DEEP_JUNGLE_GREEN)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text("Use arrow keys to move", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 240, arcade.color.CREAM,
                         font_size=30, anchor_x="center")
        arcade.draw_text("Avoid spikes, they restart the game", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 120,
                         arcade.color.CREAM, font_size=30, anchor_x="center")
        arcade.draw_text("To unlock the lock find a key", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.CREAM,
                         font_size=30, anchor_x="center")
        arcade.draw_text("Reach the exit sign, with all stars collected, to complete the level", SCREEN_WIDTH/2,
                         SCREEN_HEIGHT/2 - 120, arcade.color.CREAM, font_size=30, anchor_x="center")
        arcade.draw_text("If Rakesh does not move minimize the screen and open it again", SCREEN_WIDTH/2,
                         SCREEN_HEIGHT/2 - 240, arcade.color.CREAM, font_size=30, anchor_x="center")
        arcade.draw_text("<", 45, 695, arcade.color.CREAM, font_size=50, anchor_x="center")

        # Rectangles for the buttons
        arcade.draw_lrtb_rectangle_outline(10, 85, 760, 705, arcade.color.CREAM, 3)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if 10 < x < 85 and 705 < y < 760:
            self.window.show_view(TitleView())

class LevelView(arcade.View):
    level = 1

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.PRUSSIAN_BLUE)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text("Level 1", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 240, arcade.color.GOLDEN_POPPY, font_size=30,
                         anchor_x="center")
        arcade.draw_text("Level 2", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.GOLDEN_POPPY, font_size=30,
                         anchor_x="center")
        arcade.draw_text("Level 3", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 240, arcade.color.GOLDEN_POPPY, font_size=30,
                         anchor_x="center")
        arcade.draw_text("<", 45, 695, arcade.color.GOLDEN_POPPY, font_size=50, anchor_x="center")

        # Rectangles for the buttons
        arcade.draw_lrtb_rectangle_outline(600, 800, 670, 620, arcade.color.DEEP_JUNGLE_GREEN, 3)
        arcade.draw_lrtb_rectangle_outline(600, 800, 430, 380, arcade.color.DEEP_JUNGLE_GREEN, 3)
        arcade.draw_lrtb_rectangle_outline(600, 800, 190, 140, arcade.color.DEEP_JUNGLE_GREEN, 3)
        arcade.draw_lrtb_rectangle_outline(10, 85, 760, 705, arcade.color.DEEP_JUNGLE_GREEN, 3)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if 10 < x < 85 and 705 < y < 760:
            self.window.show_view(TitleView())

        if 600 < x < 800 and 620 < y < 670:
            LevelView.level = 1
            game_view = GameWindow()
            game_view.setup(game_view.level)
            self.window.show_view(game_view)

        if 600 < x < 800 and 380 < y < 430:
            LevelView.level = 2
            game_view = GameWindow()
            game_view.setup(game_view.level)
            self.window.show_view(game_view)

        if 600 < x < 800 and 140 < y < 190:
            LevelView.level = 3
            game_view = GameWindow()
            game_view.setup(game_view.level)
            self.window.show_view(game_view)

class GameWindow(arcade.View):
    """ Main Window """

    def __init__(self):
        """ Create the variables """

        # Init the parent class
        super().__init__()

        # Player sprite
        self.player_sprite: Optional[PlayerSprite] = None

        # Sprite lists we need
        self.player_list: Optional[arcade.SpriteList] = None
        self.wall_list: Optional[arcade.SpriteList] = None
        self.bullet_list: Optional[arcade.SpriteList] = None
        self.item_list: Optional[arcade.SpriteList] = None
        self.moving_sprites_list: Optional[arcade.SpriteList] = None
        self.moving_spikes_list: Optional[arcade.SpriteList] = None
        self.ladder_list: Optional[arcade.SpriteList] = None
        self.grab_obj: Optional[arcade.SpriteList] = None
        self.locked_obj: Optional[arcade.SpriteList] = None

        # Track the current state of what key is pressed
        self.left_pressed: bool = False
        self.right_pressed: bool = False
        self.up_pressed: bool = False
        self.down_pressed: bool = False
        self.view_bottom = 0
        self.view_left = 0
        self.score = 0
        self.stars = 0
        self.level = LevelView.level

        # Physics engine
        self.physics_engine = Optional[arcade.PymunkPhysicsEngine]

        # Set background color
        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self, level):
        """ Set up everything with the game """
        self.view_bottom = 0
        self.view_left = 0
        self.score = 0
        self.stars = 0
        self.key1_grabbed = False
        self.key2_grabbed = False
        self.key3_grabbed = False
        self.key4_grabbed = False

        # Create the sprite lists
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.coin_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/coin5.wav")
        self.stars_list = arcade.SpriteList()
        self.star_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/upgrade1.wav")
        self.spike_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/hurt2.wav")
        self.key_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/secret4.wav")
        self.bomb_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/explosion2.wav")
        self.unlock_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/upgrade3.wav")
        self.lava_sound = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/sounds/hit2.wav")
        self.congrats = arcade.load_sound("/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/venv/lib/python3.8/site-packages/arcade/resources/music/1918.mp3")

        # Read in the tiled map
        map_name = f"/Users/mahirkhandokar/Desktop/Projects/the_legend_of_rakesh/level_{level}.tmx"
        my_map = arcade.tilemap.read_tmx(map_name)
        self.background_list = arcade.tilemap.process_layer(my_map,
                                                            'Background')
        # Read in the map layers
        self.wall_list = arcade.tilemap.process_layer(my_map,
                                                      'Platforms',
                                                      SPRITE_SCALING_TILES,
                                                      hit_box_algorithm="Detailed")
        self.lock1 = arcade.tilemap.process_layer(my_map,
                                                  'Lock 1',
                                                  SPRITE_SCALING_TILES,
                                                  use_spatial_hash=True,
                                                  hit_box_algorithm="None")
        self.lock2 = arcade.tilemap.process_layer(my_map,
                                                  'Lock 2',
                                                  SPRITE_SCALING_TILES,
                                                  use_spatial_hash=True,
                                                  hit_box_algorithm="None")
        self.lock3 = arcade.tilemap.process_layer(my_map,
                                                  'Lock 3',
                                                  SPRITE_SCALING_TILES,
                                                  use_spatial_hash=True,
                                                  hit_box_algorithm="None")
        self.lock4 = arcade.tilemap.process_layer(my_map,
                                                  'Lock 4',
                                                  SPRITE_SCALING_TILES,
                                                  use_spatial_hash=True,
                                                  hit_box_algorithm="None")
        self.p_wall_list = arcade.tilemap.process_layer(my_map,
                                                        "Phasable walls",
                                                        SPRITE_SCALING_TILES,
                                                        hit_box_algorithm="Detailed")
        self.misc = arcade.tilemap.process_layer(my_map,
                                                 "Other Stuff",
                                                 SPRITE_SCALING_TILES,
                                                 hit_box_algorithm="Detailed")
        self.item_list = arcade.tilemap.process_layer(my_map,
                                                      'Dynamic Items',
                                                      SPRITE_SCALING_TILES,
                                                      hit_box_algorithm="Detailed")
        self.ladder_list = arcade.tilemap.process_layer(my_map,
                                                        'Ladders',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")
        self.coin_list = arcade.tilemap.process_layer(my_map,
                                                      "Coins",
                                                      SPRITE_SCALING_TILES,
                                                      use_spatial_hash=True,
                                                      hit_box_algorithm="Detailed")
        self.key1 = arcade.tilemap.process_layer(my_map,
                                                 "Key 1",
                                                 SPRITE_SCALING_TILES,
                                                 use_spatial_hash=True,
                                                 hit_box_algorithm="Detailed")
        self.key2 = arcade.tilemap.process_layer(my_map,
                                                 "Key 2",
                                                 SPRITE_SCALING_TILES,
                                                 use_spatial_hash=True,
                                                 hit_box_algorithm="Detailed")
        self.key3 = arcade.tilemap.process_layer(my_map,
                                                 "Key 3",
                                                 SPRITE_SCALING_TILES,
                                                 use_spatial_hash=True,
                                                 hit_box_algorithm="Detailed")
        self.key4 = arcade.tilemap.process_layer(my_map,
                                                 "Key 4",
                                                 SPRITE_SCALING_TILES,
                                                 use_spatial_hash=True,
                                                 hit_box_algorithm="Detailed")
        self.spikes = arcade.tilemap.process_layer(my_map,
                                                     "Spikes",
                                                     SPRITE_SCALING_TILES,
                                                     use_spatial_hash=True,
                                                     hit_box_algorithm="Simple")
        self.bombs = arcade.tilemap.process_layer(my_map,
                                                  "Bombs",
                                                  SPRITE_SCALING_TILES,
                                                  use_spatial_hash=True,
                                                  hit_box_algorithm="Detailed")
        self.stars_list = arcade.tilemap.process_layer(my_map,
                                                       "Stars",
                                                       SPRITE_SCALING_TILES,
                                                       use_spatial_hash=True,
                                                       hit_box_algorithm="Detailed")
        self.exit = arcade.tilemap.process_layer(my_map,
                                                 "Exit Sign",
                                                 SPRITE_SCALING_TILES,
                                                 hit_box_algorithm="Detailed")
        self.barrier = arcade.tilemap.process_layer(my_map,
                                                    "Barrier",
                                                    SPRITE_SCALING_TILES,
                                                    use_spatial_hash=True,
                                                    hit_box_algorithm="Detailed")
        self.prize = arcade.tilemap.process_layer(my_map,
                                                  "Prize",
                                                  SPRITE_SCALING_TILES,
                                                  hit_box_algorithm="Detailed")
        self.lava = arcade.tilemap.process_layer(my_map,
                                                 "Lava",
                                                 SPRITE_SCALING_TILES,
                                                 use_spatial_hash=True,
                                                 hit_box_algorithm="Detailed")

        # Create player sprite
        self.player_sprite = PlayerSprite(self.ladder_list, hit_box_algorithm="Detailed")

        # Set player location
        grid_x = 1
        grid_y = 1
        self.player_sprite.center_x = SPRITE_SIZE * grid_x + SPRITE_SIZE / 2
        self.player_sprite.center_y = SPRITE_SIZE * grid_y + SPRITE_SIZE / 2
        # Add to player sprite list
        self.player_list.append(self.player_sprite)

        # Moving Platforms
        self.moving_sprites_list = arcade.tilemap.process_layer(my_map,
                                                                'Moving Platforms',
                                                                SPRITE_SCALING_TILES)

        # Moving Spikes
        self.moving_spikes_list = arcade.tilemap.process_layer(my_map,
                                                               "Moving Spikes",
                                                               SPRITE_SCALING_TILES,
                                                               hit_box_algorithm="Simple")

        # --- Pymunk Physics Engine Setup ---

        # The default damping for every object controls the percent of velocity
        # the object will keep each second. A value of 1.0 is no speed loss,
        # 0.9 is 10% per second, 0.1 is 90% per second.
        # For top-down games, this is basically the friction for moving objects.
        # For platformers with gravity, this should probably be set to 1.0.
        # Default value is 1.0 if not specified.
        damping = DEFAULT_DAMPING

        # Set the gravity. (0, 0) is good for outer space and top-down.
        gravity = (0, -GRAVITY)

        # Create the physics engine
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping,
                                                         gravity=gravity)

        def wall_hit_handler(bullet_sprite, _wall_sprite, _arbiter, _space, _data):
            """ Called for bullet/wall collision """
            bullet_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("bullet", "wall", post_handler=wall_hit_handler)

        def item_hit_handler(bullet_sprite, item_sprite, _arbiter, _space, _data):
            """ Called for bullet/wall collision """
            bullet_sprite.remove_from_sprite_lists()
            item_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("bullet", "item", post_handler=item_hit_handler)

        # Add the player.
        # For the player, we set the damping to a lower value, which increases
        # the damping rate. This prevents the character from traveling too far
        # after the player lets off the movement keys.
        # Setting the moment to PymunkPhysicsEngine.MOMENT_INF prevents it from
        # rotating.
        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        self.physics_engine.add_sprite(self.player_sprite,
                                       friction=PLAYER_FRICTION,
                                       mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                       collision_type="player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)

        # Create the walls.
        # By setting the body type to PymunkPhysicsEngine.STATIC the walls can't
        # move.
        # Movable objects that respond to forces are PymunkPhysicsEngine.DYNAMIC
        # PymunkPhysicsEngine.KINEMATIC objects will move, but are assumed to be
        # repositioned by code and don't respond to physics forces.
        # Dynamic is default.
        self.physics_engine.add_sprite_list(self.wall_list,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.barrier,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.spikes,
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.bombs,
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.lock1,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.lock2,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.lock3,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.physics_engine.add_sprite_list(self.lock4,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Create the items
        self.physics_engine.add_sprite_list(self.item_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="item")

        # Add kinematic sprites
        self.physics_engine.add_sprite_list(self.moving_sprites_list,
                                            body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

        self.physics_engine.add_sprite_list(self.moving_spikes_list,
                                            body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.UP:
            self.up_pressed = True
            # find out if player is standing on ground, and not on a ladder
            if self.physics_engine.is_on_ground(self.player_sprite) \
                    and not self.player_sprite.is_on_ladder:
                # She is! Go ahead and jump
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.physics_engine.apply_impulse(self.player_sprite, impulse)
        elif key == arcade.key.DOWN:
            self.down_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called whenever the mouse button is clicked. """

        bullet = BulletSprite(20, 5, arcade.color.DARK_YELLOW)
        self.bullet_list.append(bullet)

        # Position the bullet at the player's current location
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y
        bullet.position = self.player_sprite.position

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x = x
        dest_y = y

        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # What is the 1/2 size of this sprite, so we can figure out how far
        # away to spawn the bullet
        size = max(self.player_sprite.width, self.player_sprite.height) / 2

        # Use angle to to spawn bullet away from player in proper direction
        bullet.center_x += size * math.cos(angle)
        bullet.center_y += size * math.sin(angle)

        # Set angle of bullet
        bullet.angle = math.degrees(angle)

        # Gravity to use for the bullet
        # If we don't use custom gravity, bullet drops too fast, or we have
        # to make it go too fast.
        # Force is in relation to bullet's angle.
        bullet_gravity = (0, -BULLET_GRAVITY)

        # Add the sprite. This needs to be done AFTER setting the fields above.
        self.physics_engine.add_sprite(bullet,
                                       mass=BULLET_MASS,
                                       damping=1.0,
                                       friction=0.6,
                                       collision_type="bullet",
                                       gravity=bullet_gravity,
                                       elasticity=0.9)
        # Add force to bullet
        force = (BULLET_MOVE_FORCE, 0)
        self.physics_engine.apply_force(bullet, force)

    def on_update(self, delta_time):
        """ Movement and game logic """
        is_on_ground = self.physics_engine.is_on_ground(self.player_sprite)
        # Update player forces based on keys pressed
        if self.left_pressed and not self.right_pressed:
            # Create a force to the left. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.right_pressed and not self.left_pressed:
            # Create a force to the right. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.up_pressed and not self.down_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.down_pressed and not self.up_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, -PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)

        else:
            # Player's feet are not moving. Therefore up the friction so we stop.
            self.physics_engine.set_friction(self.player_sprite, 1.0)

        # Move items in the physics engine
        self.physics_engine.step()

        # For each moving sprite, see if we've reached a boundary and need to
        # reverse course.
        for moving_sprite in self.moving_sprites_list:
            if moving_sprite.boundary_right and \
                    moving_sprite.change_x > 0 and \
                    moving_sprite.right > moving_sprite.boundary_right:
                moving_sprite.change_x *= -1
            elif moving_sprite.boundary_left and \
                    moving_sprite.change_x < 0 and \
                    moving_sprite.left > moving_sprite.boundary_left:
                moving_sprite.change_x *= -1
            if moving_sprite.boundary_top and \
                    moving_sprite.change_y > 0 and \
                    moving_sprite.top > moving_sprite.boundary_top:
                moving_sprite.change_y *= -1
            elif moving_sprite.boundary_bottom and \
                    moving_sprite.change_y < 0 and \
                    moving_sprite.bottom < moving_sprite.boundary_bottom:
                moving_sprite.change_y *= -1

            # Figure out and set our moving platform velocity.
            # Pymunk uses velocity is in pixels per second. If we instead have
            # pixels per frame, we need to convert.
            velocity = (moving_sprite.change_x * 1 / delta_time, moving_sprite.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(moving_sprite, velocity)

        for moving_sprite in self.moving_spikes_list:
            if moving_sprite.boundary_right and \
                    moving_sprite.change_x > 0 and \
                    moving_sprite.right > moving_sprite.boundary_right:
                moving_sprite.change_x *= -1
            elif moving_sprite.boundary_left and \
                    moving_sprite.change_x < 0 and \
                    moving_sprite.left > moving_sprite.boundary_left:
                moving_sprite.change_x *= -1
            if moving_sprite.boundary_top and \
                    moving_sprite.change_y > 0 and \
                    moving_sprite.top > moving_sprite.boundary_top:
                moving_sprite.change_y *= -1
            elif moving_sprite.boundary_bottom and \
                    moving_sprite.change_y < 0 and \
                    moving_sprite.bottom < moving_sprite.boundary_bottom:
                moving_sprite.change_y *= -1

            velocity = (moving_sprite.change_x * 1 / delta_time, moving_sprite.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(moving_sprite, velocity)

        self.coin_list.update_animation(delta_time)
        coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)

        for coin in coin_hit_list:
            self.score += len(coin_hit_list)
            arcade.play_sound(self.coin_sound)
            coin.remove_from_sprite_lists()

        self.stars_list.update_animation(delta_time)
        star_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.stars_list)

        for star in star_hit_list:
            self.stars += len(star_hit_list)
            arcade.play_sound(self.star_sound)
            star.remove_from_sprite_lists()

        self.key1.update_animation(delta_time)
        key_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.key1)

        if not self.key1_grabbed:
            if key_hit_list:
                arcade.play_sound(self.key_sound)
        if len(key_hit_list) > 0:
            self.key1_grabbed = True
        if len(key_hit_list) == 0:
            self.key1_grabbed = False

        for key in key_hit_list:
            key.position = self.player_sprite.position

        self.lock1.update_animation(delta_time)

        if len(self.lock1) == 1 and len(self.key1) == 1:
            if arcade.check_for_collision(self.key1[0], self.lock1[0]):
                self.lock1[0].remove_from_sprite_lists()
                self.key1[0].remove_from_sprite_lists()

        self.key2.update_animation(delta_time)
        key_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.key2)

        if not self.key2_grabbed:
            if key_hit_list:
                arcade.play_sound(self.key_sound)
        if len(key_hit_list) > 0:
            self.key2_grabbed = True
        if len(key_hit_list) == 0:
            self.key2_grabbed = False

        for key in key_hit_list:
            key.position = self.player_sprite.position

        self.lock2.update_animation(delta_time)

        if len(self.lock2) == 1 and len(self.key2) == 1:
            if arcade.check_for_collision(self.key2[0], self.lock2[0]):
                self.lock2[0].remove_from_sprite_lists()
                self.key2[0].remove_from_sprite_lists()

        self.key3.update_animation(delta_time)
        key_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.key3)

        if not self.key3_grabbed:
            if key_hit_list:
                arcade.play_sound(self.key_sound)
        if len(key_hit_list) > 0:
            self.key3_grabbed = True
        if len(key_hit_list) == 0:
            self.key3_grabbed = False

        for key in key_hit_list:
            key.position = self.player_sprite.position

        self.lock3.update_animation(delta_time)

        if len(self.lock3) == 1 and len(self.lock3) == 1:
            if arcade.check_for_collision(self.key3[0], self.lock3[0]):
                self.lock3[0].remove_from_sprite_lists()
                self.key3[0].remove_from_sprite_lists()

        self.key4.update_animation(delta_time)
        key_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.key4)

        if not self.key4_grabbed:
            if key_hit_list:
                arcade.play_sound(self.key_sound)
        if len(key_hit_list) > 0:
            self.key4_grabbed = True
        if len(key_hit_list) == 0:
            self.key4_grabbed = False

        for key in key_hit_list:
            key.position = self.player_sprite.position

        self.lock4.update_animation(delta_time)

        if len(self.lock4) == 1 and len(self.key4) == 1:
            if arcade.check_for_collision(self.key4[0], self.lock4[0]):
                self.lock4[0].remove_from_sprite_lists()
                self.key4[0].remove_from_sprite_lists()

        if arcade.check_for_collision_with_list(self.player_sprite, self.spikes):
            arcade.play_sound(self.spike_sound)
            self.setup(self.level)

        if arcade.check_for_collision_with_list(self.player_sprite, self.bombs):
            arcade.play_sound(self.bomb_sound)
            self.setup(self.level)

        if arcade.check_for_collision_with_list(self.player_sprite, self.moving_spikes_list):
            arcade.play_sound(self.spike_sound)
            self.setup(self.level)

        if arcade.check_for_collision_with_list(self.player_sprite, self.lava):
            arcade.play_sound(self.lava_sound)
            self.setup(self.level)

        changed_viewport = False

        if len(self.stars_list) == 0:
            if arcade.check_for_collision_with_list(self.player_sprite, self.prize):
                os._exit(1)

        if len(self.stars_list) == 0:
            if arcade.check_for_collision_with_list(self.player_sprite, self.exit):
                self.level += 1
                self.setup(self.level)
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True

        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed_viewport = True
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed_viewport = True
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed_viewport = True
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed_viewport = True
        if changed_viewport:
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)

    def on_draw(self):
        """ Draw everything """
        arcade.start_render()
        self.background_list.draw()
        self.ladder_list.draw()
        self.moving_sprites_list.draw()
        self.bullet_list.draw()
        self.item_list.draw()
        self.misc.draw()
        self.exit.draw()
        self.prize.draw()
        self.lock1.draw()
        self.key1.draw()
        self.lock2.draw()
        self.key2.draw()
        self.lock3.draw()
        self.key3.draw()
        self.lock4.draw()
        self.key4.draw()
        self.player_list.draw()
        self.coin_list.draw()
        self.stars_list.draw()
        self.bombs.draw()
        self.p_wall_list.draw()
        self.spikes.draw()
        self.moving_spikes_list.draw()
        self.lava.draw()
        self.wall_list.draw()

        score = f"Score: {self.score}"
        arcade.draw_text(score, 10 + self.view_left, 10 + self.view_bottom, arcade.color.BLACK, 14)
        stars = f"Stars: {self.stars}"
        arcade.draw_text(stars, 110 + self.view_left, 10 + self.view_bottom, arcade.color.BLACK, 14)

def main():
    """ Main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, False, True)
    window.show_view(TitleView())
    arcade.run()

if __name__ == "__main__":
    main()