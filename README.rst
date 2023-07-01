Performance tests to display camera preview on Pygame window
------------------------------------------------------------

1. Flip the entire screen (preview same size than screen)
    
Script : `use_flip.py`
Avg FPS on OSX (20 cycle): 73.53
Avg FPS on RPi3(20 cycle): ?

Avg FPS on OSX (200 cycle): 98.04
Avg FPS on RPi3(200 cycle): ?

2. Update only preview rect (smaller than screen)

Script : `use_update.py`
Avg FPS on OSX (20 cycle): 76.34
Avg FPS on RPi3(20 cycle): ?

Avg FPS on OSX (200 cycle): 98.04
Avg FPS on RPi3(200 cycle): ?

3. Update only preview rect on camera event

Script : `use_update_on_event.py`
Avg FPS on OSX (20 cycle): 93.46
Avg FPS on RPi3(20 cycle): ?

Avg FPS on OSX (200 cycle): 90.91
Avg FPS on RPi3(200 cycle): ?

4. Update only preview rect on camera event using dirty concept

Script : `use_update_dirty_on_event.py`
Avg FPS on OSX (20 cycle): 93.46
Avg FPS on RPi3(20 cycle): ?

Avg FPS on OSX (200 cycle): 91.74
Avg FPS on RPi3(200 cycle): ?