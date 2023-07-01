
import threading
from concurrent import futures
from functools import partial
from itertools import cycle
import pygame
import numpy
from PIL import ImageOps


CAM_EVENT = pygame.USEREVENT + 201


class AsyncTasksPool:

    """Class to manage a pool of asynchronous tasks.
    """

    FUTURES = {}

    def __init__(self):
        if not AsyncTask.POOL:
            self._pool = futures.ThreadPoolExecutor()
            AsyncTask.POOL = self
        else:
            self._pool = AsyncTask.POOL._pool
        self._pool.stop_event = threading.Event()

    def start_task(self, task):
        """Start an asynchronous task and add future on tracking list.
        """
        if self._pool.stop_event.is_set():
            raise RuntimeError("AsyncTasksPool is shutting down")
        assert isinstance(task, AsyncTask)
        future = self._pool.submit(task)
        self.FUTURES[future] = task
        future.add_done_callback(self.finish_task)
        return future

    def finish_task(self, future):
        """Remove future from tracking list.
        """
        self.FUTURES.pop(future)

    def quit(self):
        """Stop all tasks and don't accept new one.
        """
        self._pool.stop_event.set()
        for task in self.FUTURES.copy().values():
            task.kill()
        self.FUTURES.clear()
        self._pool.shutdown(wait=True)


class AsyncTask:

    """Class to execute an asynchronous task.

    :param runnable: a callable object to execute asynchronously:
    :type runnable: callable
    :param args: arguments to pass to the runnable
    :type args: tuple, list
    :param event: a event to post (with 'result') at task end
    :type event: int
    :param loop: execute the runnable in an infinit loop if True
    :type loop: bool
    """

    POOL = None

    def __init__(self, runnable, args=(), event=None, loop=False):
        if not self.POOL:
            raise EnvironmentError("Tasks pool is not initialized.")
        self._stop_event = threading.Event()
        self.runnable = runnable
        self.args = args
        self.event_type = event
        self.loop = loop
        self.future = self.POOL.start_task(self)

    def __call__(self):
        """Execute the runnable.
        """
        result = None
        while not self._stop_event.is_set():
            try:
                result = self.runnable(*self.args)
                self.emit(result)
                if not self.loop:
                    break
            except Exception as ex:
                self.emit(None, ex)
                break
        return result

    def emit(self, data, exception=None):
        """Post event with the result of the task.
        """
        if self.event_type is not None:
            pygame.event.post(pygame.event.Event(self.event_type, result=data, exception=exception))

    def result(self):
        """Return task result or None if task is not finished.
        """
        try:
            return self.future.result(timeout=0.01)
        except futures.TimeoutError:
            return None

    def is_alive(self):
        """Return true if the task is not yet started or running.
        """
        return not self.future.done()

    def wait(self, timeout=None):
        """Wait for task ends or cancelled and return the result.
        """
        return self.future.result(timeout)

    def kill(self):
        """Stop running.
        """
        self._stop_event.set()
        self.future.cancel()
        try:
            self.wait(10)  # Max 10 seconds
        except Exception as ex:
            print("AsyncTask.kill() failed: %s", ex)


class LibcameraCameraProxyMock:

    class Transform:

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    def __init__(self, fake_captures):
        self._take = cycle(fake_captures)
        self.sensor_resolution = fake_captures[0].size
        self.config = None

    def create_preview_configuration(self):
        return {'type': 'preview', 'main': {}}

    def create_still_configuration(self):
        return {'type': 'still', 'main': {'size': self.sensor_resolution}}

    def configure(self, config):
        self.config = config

    def start(self):
        pass

    def stop(self):
        pass

    def capture_array(self, channel='main'):
        return numpy.asarray(ImageOps.fit(next(self._take), self.config[channel]['size']))

    def capture_image(self, channel='main'):
        return ImageOps.fit(next(self._take), self.config[channel]['size'])

    def switch_mode_and_capture_image(self, config, channel='main'):
        old_config = self.config
        self.config = config
        image = self.capture_image(channel)
        self.config = old_config
        return image


try:
    from picamera2 import Picamera2
except ImportError:
    import os.path as osp
    from PIL import Image
    images_path = osp.join(osp.dirname(osp.abspath(osp.dirname(__file__))), 'images')
    Picamera2 = partial(LibcameraCameraProxyMock, [Image.open(osp.join(images_path, 'capture0.jpeg')),
                                                   Image.open(osp.join(images_path, 'capture1.jpeg'))])


def create_camera(size):
    camera = Picamera2()

    preview_config = camera.create_preview_configuration()
    preview_config['main']['size'] = size
    preview_config['main']['format'] = 'BGR888'

    capture_config = camera.create_still_configuration()
    capture_config['main']['size'] = camera.sensor_resolution

    camera.configure(preview_config)
    return camera, capture_config
