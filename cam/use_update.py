
import time
import logging
import pygame
from .utils import create_camera


class Game:

    def __init__(self, display_size, preview_size):
        self.preview_size = preview_size
        self.display_size = display_size
        self.camera, self.capture_config = create_camera(self.preview_size)
        self.camera.start()
        self.capture_display_time = 3

    def update(self, screen, events):
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

        array = self.camera.capture_array()
        surface = pygame.image.frombuffer(array.data, self.preview_size, 'RGB')
        rect = surface.get_rect(center=screen.get_rect().center)
        screen.blit(surface, rect.topleft)

        # Update only the surface where preview is displayed
        pygame.display.update([rect])

    def quit(self):
        self.camera.stop()