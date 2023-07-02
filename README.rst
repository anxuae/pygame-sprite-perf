Performance tests to display camera preview on Pygame window
------------------------------------------------------------

Config
++++++

`OSX`  : pygame 2.4.0 (SDL 2.26.4, Python 3.8.9) + Picamera2 mock

`RPi3` : pygame 2.4.0 (SDL 2.0.14, Python 3.9.2) + Picamera2 connected to HQ camera

Tests
+++++

1. Flip the entire screen (preview same size than screen)
    
Script: `use_flip.py`

======= ======== =========
Cycles  FPS OSX  FPS RPi3
======= ======== =========
20      76.34    16.89
200     94.34    28.17
400     95.24    15.10
======= ======== =========

2. Update only preview rect (smaller than screen)

Script: `use_update.py`

======= ======== =========
Cycles  FPS OSX  FPS RPi3
======= ======== =========
20      76.92    20.88
200     98.04    14.54
400     98.04    15.01
======= ======== =========

3. Update only preview rect on camera event

Script: `use_update_on_event.py`

======= ======== =========
Cycles  FPS OSX  FPS RPi3
======= ======== =========
20      94.34    31.64
200     90.91    58.14
400     92.59    96.15
======= ======== =========

4. Update only preview rect on camera event using dirty concept

Script: `use_update_dirty_on_event.py`

======= ======== =========
Cycles  FPS OSX  FPS RPi3
======= ======== =========
20      97.09    68.49
200     91.74    86.21
400     93.46    84.03
======= ======== =========