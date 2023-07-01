
import time
import logging

from functools import partial
import pygame
from .utils import create_camera, AsyncTasksPool, AsyncTask, CAM_EVENT


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
    """Return a new size included (if resize_type='inner') or excluded (if resize_type='outer')
    in the targeted one by resizing and keeping the original image's aspect ratio.
    """
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
    """Return a tuple of top-left and bottom-right points (x1, y1, x2, y2) coresponding
    to a crop of the original size keeping the same aspect ratio of the target size.

    Note: target_size is only used to calculate aspect ratio, the returned coordinates
          doesn't fit to it.

    The position of the rectangle can be defined by the crop_type parameter:

       * top-left
       * top-center
       * top-right
       * center-left
       * center
       * center-right
       * bottom-left
       * bottom-center
       * bottom-right
    """
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
    """Resize a Pygame surface, the image is resized keeping the original
    surface's aspect ratio.

    :param surface: Pygame surface to resize
    :type surface: object
    :param size: resize image to this size
    :type size: tuple
    :param antialiasing: use antialiasing algorithm when resize
    :type antialiasing: bool
    :param hflip: apply an horizontal flip
    :type hflip: bool
    :param vflip: apply a vertical flip
    :type vflip: bool
    :param crop: crop image to fit the size keeping aspect ratio
    :type crop: bool
    :param angle: angle of rotation of the image
    :type angle: int
    :param color: recolorize image
    :type color: tuple

    :return: pygame.Surface with image
    :rtype: object
    """
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


def image2surface(image, size):
    surface = pygame.image.frombuffer(image.tobytes(), image.size, image.mode)
    return transform_pygame_image(surface, size, hflip=False,
                                  vflip=False, angle=0, crop=False,
                                  color=None)


class Game:

    def __init__(self, display_size, preview_size):
        self.preview_size = preview_size
        self.display_size = display_size
        self.camera, self.capture_config = create_camera(self.preview_size)
        self.camera.start()
        self.capture_display_time = 3
        self.pool = AsyncTasksPool()
        self.worker = AsyncTask(partial(get_preview_image, self.camera), event=CAM_EVENT, loop=True)

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

            if (event.type == CAM_EVENT):
                surface = image2surface(event.result, self.preview_size)
                rect = surface.get_rect(center=screen.get_rect().center)
                screen.blit(surface, rect.topleft)
                dirty_rects.append(rect)

        pygame.display.update(dirty_rects)

    def quit(self):
        self.pool.quit()
        self.camera.stop()
