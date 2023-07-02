
import time
import logging
import pygame
import cProfile
import pstats
from pstats import SortKey
import argparse


DISPLAY_SIZE = (800, 480)
PREVIEW_SIZE = (240, 400)


def pygame_loop(game, profile=False, loop_count=None):
    counter = 0
    start_time = time.time()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(DISPLAY_SIZE)

    if profile:
        profiler = cProfile.Profile()

    while True:
        events = pygame.event.get()

        for event in events:
            # Press "ESC" key -> exit
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                logging.info("Game loop speed (FPS): %s", clock.get_fps())
                logging.info("Capture per seconds (CPS): %s", game.capture_counter / (time.time() - start_time))
                return

        if profile:
            profiler.enable()

        game.update(screen, events)

        if profile:
            profiler.dump_stats(f"prof{counter}.dump")
            p = pstats.Stats(f"prof{counter}.dump")
            p.sort_stats(SortKey.TIME).print_stats(3)

        if loop_count and counter >= loop_count:
            logging.info("Game loop speed (FPS): %s", clock.get_fps())
            logging.info("Capture per seconds (CPS): %s", game.capture_counter / (time.time() - start_time))
            break

        clock.tick(100)  # Ensure not exceed 100 FPS
        counter += 1


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

    parser = argparse.ArgumentParser(
                        prog='tester',
                        description='Test to update Pygame window as fast as possible')
    parser.add_argument('filename')
    parser.add_argument('-c', '--count', type=int, default=0)
    parser.add_argument('-p', '--profile', default=False, action='store_true')
    args = parser.parse_args()

    if "use_flip.py" in args.filename:
        from cam.use_flip import Game
    elif "use_update.py" in args.filename:
        from cam.use_update import Game
    elif "use_update_on_event.py" in args.filename:
        from cam.use_update_on_event import Game
    elif "use_update_dirty_on_event.py" in args.filename:
        from cam.use_update_dirty_on_event import Game
    else:
        raise NotImplementedError(args.filename)

    pygame.init()
    game = Game(DISPLAY_SIZE, PREVIEW_SIZE)
    pygame_loop(game, profile=args.profile, loop_count=args.count)
    game.quit()
    pygame.quit()
