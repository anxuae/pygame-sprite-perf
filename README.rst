Performance tests to display camera preview on Pygame window
------------------------------------------------------------

Config
++++++

`OSX`  : pygame 2.4.0 (SDL 2.26.4, Python 3.8.9) + Picamera2 mock

`RPi3` : pygame 2.4.0 (SDL 2.0.14, Python 3.9.2) + Picamera2 connected to HQ camera

Tests
+++++

Test performed to monitor the game loop speed (FPS) and camera capture per seconds
(CPS).

1. Flip the entire screen (preview same size than screen)
    
Script: `use_flip.py`

======= ============ ============
Cycles  FPS/CPS OSX  FPS/CPS RPi3
======= ============ ============
20      72/28        
200     97/77        
400     97/84        
======= ============ ============

2. Update only preview rect (smaller than screen)

Script: `use_update.py`

======= ============ ============
Cycles  FPS/CPS OSX  FPS/CPS RPi3
======= ============ ============
20      75/28        
200     95/76        
400     98/86        
======= ============ ============

3. Update only preview rect on camera event

Script: `use_update_on_event.py`

======= ============ ============
Cycles  FPS/CPS OSX  FPS/CPS RPi3
======= ============ ============
20      94/24        
200     93/78        
400     92/91        
======= ============ ============

4. Update only preview rect on camera event using dirty concept

Script: `use_update_dirty_on_event.py`

======= ============ ============
Cycles  FPS/CPS OSX  FPS/CPS RPi3
======= ============ ============
20      95/23        
200     91/82        
400     90/93        
======= ============ ============