import PIL

import time
import logging
from functools import partial

import pygame
from .utils import create_camera, AsyncTasksPool, AsyncTask, CAM_EVENT


class BaseSprite(pygame.sprite.DirtySprite):

    """Base sprite for any graphical element. It handles common attributes
    and methods:
      - show/hide: manage when sprite is displayed
      - color: manage color rendering
      - resizing: manage pygame.Rect dimension
      - outline: manage a colored rectangle around the sprite
      - event: manage pressed action

    A sprite can be composed it-self with other sprites (called sub-sprites).
    For instance, the outlines are sub-sprites.
    """

    def __init__(self, parent=None, size=(10, 10), outlines=True, layer=None):
        """
        :param parent: sprite on which outlines are drawn
        :type parent: object
        :param size: size tuple (width, height) of the image
        :type size: tuple
        :param outlines: enable oulines on current rect sprite
        :type outlines: bool
        :param layer: layer number used to order draw actions
        :type layer: int
        """
        super().__init__()
        self._image_cache = None
        self._subsprites = []  # Sub-sprites composing the sprite
        self.parent = parent
        self.rect = pygame.Rect((0, 0), size)
        self.color = None
        self.pressed = 0
        self.on_pressed = None
        self.layer = layer
        if self.parent:
            self.parent.add_sprite(self)

    def get_sprites(self, include_outlines=True, recursive=False):
        """Return all sub-sprites.
        """
        if recursive:
            sprites = []
            sprites.extend(self._subsprites)
            for sprite in self._subsprites:
                sprites += sprite.get_sprites(include_outlines, recursive)
            return sprites
        elif not include_outlines:
            return [sprite for sprite in self._subsprites if not isinstance(sprite, OutlinesSprite)]
        else:
            return self._subsprites

    def draw(self):
        """Render sprite image.

        :return: image for the sprite
        :rtype: Pygame surface
        """
        raise NotImplementedError

    @property
    def image(self):
        """Return current sprite image.
        """
        if not self._image_cache:
            self._image_cache = self.draw()
        return self._image_cache

    def set_dirty(self, redraw=True):
        """Set current image.
        """
        self.dirty = 1
        if redraw:
            self._image_cache = None

    def add_sprite(self, sprite):
        """Add a sub-sprite to compose the sprite.
        """
        assert isinstance(sprite, BaseSprite), f"Sub-sprite '{sprite}' shall inherite from 'BaseSprite' class"
        if sprite.parent == self:
            # Register direct sprites
            self._subsprites.append(sprite)
        if self.parent:
            # Propagate to parent
            self.parent.add_sprite(sprite)
        return sprite

    def show(self):
        """Show sprite.
        """
        if not self.visible:
            self.visible = 1
            for sprite in self.get_sprites():
                sprite.show()

    def hide(self):
        """Hide sprite.
        """
        if self.visible:
            self.visible = 0
            for sprite in self.get_sprites():
                sprite.hide()

    def set_rect(self, x, y, width, height):
        """Set the sprite absolute position and size.

        :param x: position x
        :type x: int
        :param y: position y
        :type y: int
        :param width: background width
        :type width: int
        :param height: background height
        :type height: int
        """
        assert width > 0, "Sprite width shall be greater than zero"
        assert height > 0, "Sprite height shall be greater than zero"
        if self.rect.topleft != (int(x), int(y)):
            self.rect.topleft = (x, y)
            self.set_dirty(False)
        if self.rect.size != (int(width), int(height)):
            self.rect.size = (width, height)
            self.set_dirty()

    def set_color(self, color):
        """Re-colorize the skin.

        :param color: RGB color tuple
        :type color: tuple
        """
        if color != self.color:
            self.color = color
            self.set_dirty()

    def get_color(self, factor=1):
        """Return image main color.

        :param factor: more or less dark, should be > 0 and < 1
        :type factor: int
        """
        if self.color:
            return tuple(min(int(c * abs(factor)), 255) for c in self.color)
        return pygame.transform.average_color(self.image)

    def set_pressed(self, state):
        """Set the pressed state (1 for pressed 0 for released)
        and redraws it.

        :param state: new sprite state.
        :type state: bool.
        """
        if self.pressed != int(state):
            self.pressed = int(state)
            if self.on_pressed is not None:
                if self.pressed and self.visible:
                    self.visible = 0
                elif not self.pressed and not self.visible:
                    self.visible = 1
                    # Trigger callback when press is released
                    self.on_pressed()


class ImageSprite(BaseSprite):

    """Image Sprite. Handle transformation on a source image which can be:
     - RGB color tuple
     - path to an image
     - PIL image object
     - Pygame surface object
    """

    def __init__(self, parent, skin=None, colorize=True, **kwargs):
        """
        :param parent: sprite to which current sprite is linked
        :type parent: object
        :param skin: image file path, RGB color tuple,  PIL image or Pygame surface
        :type skin: str or tuple or object
        :param colorize: recolorize picture if a color is set.
        :type colorize: tuple
        """
        kwargs['layer'] = kwargs.get('layer', 2)
        super().__init__(parent, **kwargs)
        self._image_orig = None
        self.path = None
        self.crop = False
        self.hflip = False
        self.vflip = False
        self.angle = 0
        self.colorize = colorize
        if skin:
            self.set_skin(skin)

    def __repr__(self):
        if self.path:
            elem = f"path='{osp.basename(self.path)}'"
        else:
            elem = f"image={self._image_orig}"
        return f"{self.__class__.__name__}({elem}, rect={tuple(self.rect)})"

    def draw(self):
        """Render image.
        """
        if self._image_orig is None:
            if self.path:
                self._image_orig = load_pygame_image(self.path)
            else:
                raise ValueError(f"Path to image is missing for '{self}'")

        if isinstance(self._image_orig, (tuple, list)):
            image = pygame.Surface(self.rect.size, pygame.SRCALPHA, 32)
            image.fill(self._image_orig)
            return image
        elif isinstance(self._image_orig, PIL.Image.Image):
            surface = pygame.image.frombuffer(self._image_orig.tobytes(),
                                              self._image_orig.size, self._image_orig.mode)
            return transform_pygame_image(surface, self.rect.size, hflip=self.hflip,
                                          vflip=self.vflip, angle=self.angle, crop=self.crop,
                                          color=self.color if self.colorize else None)
        else:
            return transform_pygame_image(self._image_orig, self.rect.size, hflip=self.hflip,
                                          vflip=self.vflip, angle=self.angle, crop=self.crop,
                                          color=self.color if self.colorize else None)

    def set_skin(self, skin):
        """Set skin used to fill the sprite. Skin can be:

            - RGB color tuple
            - path to an image
            - PIL image object
            - Pygame surface object

        :param skin: image file path, RGB color tuple,  PIL image or Pygame surface
        :type skin: str or tuple or object
        """
        if isinstance(skin, str):
            if skin != self.path:
                self.path = skin
                self._image_orig = None
                self.set_dirty()
        elif isinstance(skin, (tuple, list)):
            assert len(skin) == 3, "Length of 3 is required for RGB tuple"
            if skin != self._image_orig:
                self.path = None
                self._image_orig = skin
                self.set_dirty()
        else:
            assert isinstance(skin, (PIL.Image.Image, pygame.Surface)), "PIL Image or Pygame Surface is required"
            if skin != self._image_orig:
                self.path = None
                self._image_orig = skin
                self.set_dirty()

    def get_skin(self):
        """Return the current skin.
        """
        return self.path or self._image_orig

    def set_crop(self, crop=True):
        """Crop the skin to fit sprite size.

        :param crop: crop image to fit aspect ratio of the size
        :type crop: bool
        """
        if crop != self.crop:
            self.crop = crop
            self.set_dirty()

    def set_flip(self, hflip=None, vflip=None):
        """Flip the skin vertically or horizontally.

        :param hflip: apply an horizontal flip
        :type hflip: bool
        :param vflip: apply a vertical flip
        :type vflip: bool
        """
        if hflip is not None and hflip != self.hflip:
            self.hflip = hflip
            self.set_dirty()
        if vflip is not None and vflip != self.vflip:
            self.vflip = vflip
            self.set_dirty()

    def set_angle(self, angle=0):
        """Rotate the skin.

        :param angle: angle of rotation of the image
        :type angle: int
        """
        if angle != self.angle:
            self.angle = angle
            self.set_dirty()


def get_preview_image(camera):
    return camera.capture_image('main')


def colorize_pygame_image(surface, color):
    surface = surface.copy()
    # zero out RGB values
    surface.fill((0, 0, 0, 255), None, pygame.BLEND_RGBA_MULT)
    # add in new RGB values
    surface.fill(color[0:3] + (0,), None, pygame.BLEND_RGBA_ADD)
    return surface


def new_size_keep_aspect_ratio(original_size, target_size, resize_type='inner'):
    # Get current and desired ratio for the images
    img_ratio = original_size[0] / float(original_size[1])
    ratio = target_size[0] / float(target_size[1])

    ox, oy = original_size
    tx, ty = target_size

    if ratio > img_ratio:
        # fit to width
        scale_factor = target_size[0] / float(ox)
        ty = scale_factor * oy
        if ty > target_size[1] and resize_type == 'inner':
            scale_factor = target_size[1] / float(oy)
            tx = scale_factor * ox
            ty = target_size[1]
    elif ratio < img_ratio:
        # fit to height
        scale_factor = target_size[1] / float(oy)
        tx = scale_factor * ox
        if tx > target_size[0] and resize_type == 'inner':
            scale_factor = target_size[0] / float(ox)
            tx = target_size[0]
            ty = scale_factor * oy
    return (int(tx), int(ty))


def new_size_by_croping_ratio(original_size, target_size, crop_type='center'):
    # Get current and desired ratio for the images
    img_ratio = original_size[0] / float(original_size[1])
    ratio = target_size[0] / float(target_size[1])

    tx, ty = original_size
    if ratio > img_ratio:
        # crop on constant width
        ty = int(original_size[0] / ratio)
    elif ratio < img_ratio:
        # crop on constant height
        tx = int(ratio * original_size[1])

    x, y = 0, 0
    if crop_type.endswith('left'):
        x = 0
    elif crop_type.endswith('center'):
        x = (original_size[0] - tx) // 2
    elif crop_type.endswith('right'):
        x = original_size[0] - tx

    if crop_type.startswith('top'):
        y = 0
    elif crop_type.startswith('center'):
        y = (original_size[1] - ty) // 2
    elif crop_type.startswith('bottom'):
        y = original_size[1] - ty

    return (x, y, tx + x, ty + y)


def transform_pygame_image(surface, size, antialiasing=True, hflip=False, vflip=False,
                           angle=0, crop=False, color=None):
    if crop:
        resize_type = 'outer'
    else:
        resize_type = 'inner'

    if angle != 0:
        surface = pygame.transform.rotate(surface, angle)

    if size != surface.get_size():
        if antialiasing:
            image = pygame.transform.smoothscale(
                surface, new_size_keep_aspect_ratio(surface.get_size(), size, resize_type))
        else:
            image = pygame.transform.scale(surface, new_size_keep_aspect_ratio(
                surface.get_size(), size, resize_type))
    else:
        image = surface.copy()

    if crop and size != image.get_size():
        # Crop image to fill surface
        new_surface = pygame.Surface(size, pygame.SRCALPHA, 32)
        new_surface.blit(image, (0, 0), new_size_by_croping_ratio(image.get_rect().size, size))
        image = new_surface
    elif size != image.get_size():
        # Center image on surface
        new_surface = pygame.Surface(size, pygame.SRCALPHA, 32)
        new_surface.blit(image, image.get_rect(center=new_surface.get_rect().center))
        image = new_surface

    if hflip or vflip:
        image = pygame.transform.flip(image, hflip, vflip)
    if color:
        image = colorize_pygame_image(image, color)
    return image


class Game:

    def __init__(self, display_size, preview_size):
        self.preview_size = preview_size
        self.display_size = display_size
        self.camera, self.capture_config = create_camera(self.preview_size)
        self.camera.start()
        self.capture_display_time = 3
        self.capture_counter = 0
        self.pool = AsyncTasksPool()
        self.worker = AsyncTask(partial(get_preview_image, self.camera), event=CAM_EVENT, loop=True)

        self.sprites = pygame.sprite.LayeredDirty()
        image = ImageSprite(None, layer=3)
        image.set_rect((self.display_size[0] - self.preview_size[0]) // 2,
                       (self.display_size[1] - self.preview_size[1]) // 2,
                       self.preview_size[0], self.preview_size[1])
        image.hide()
        self.sprites.add(image)

        self.background = ImageSprite(None, (0, 0, 0), size=self.display_size, outlines=False, layer=0)
        self.background.set_rect(0, 0, self.display_size[0], self.display_size[1])
        #self.sprites.clear(None, self.background.image)

    def update(self, screen, events):
        dirty_rects = []

        for event in events:
            # Press "space" key -> capture image
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                logging.info("Capture image")
                image = self.camera.switch_mode_and_capture_image(self.capture_config, 'main')
                image.save("test.jpg")
                logging.info("Display image")
                surface = pygame.image.frombuffer(image.tobytes(), image.size, image.mode).convert()
                rect = surface.get_rect()
                screen.blit(surface, rect)
                pygame.display.update([rect])
                logging.info("Wait for %ss", self.capture_display_time)
                time.sleep(self.capture_display_time)

            if event.type == CAM_EVENT:
                self.sprites.get_sprite(0).set_skin(event.result)
                self.sprites.get_sprite(0).show()
                self.capture_counter += 1

        self.sprites.update(events)
        dirty_rects = self.sprites.draw(screen)
        pygame.display.update(dirty_rects)

    def quit(self):
        self.pool.quit()
        self.camera.stop()
