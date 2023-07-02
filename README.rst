Performance tests to display camera preview on Pygame window
------------------------------------------------------------

1. Flip the entire screen (preview same size than screen)
    
    Script: `use_flip.py`

    +------+--------+--------+
    |Cycles|FPS OSX |FPS RPi3|
    +------+--------+--------+
    |20    |76.34   |        |
    |200   |94.34   |        |
    +------+--------+--------+

2. Update only preview rect (smaller than screen)

    Script: `use_update.py`

    +------+--------+--------+
    |Cycles|FPS OSX |FPS RPi3|
    +------+--------+--------+
    |20    |76.92   |        |
    |200   |98.04   |        |
    +------+--------+--------+

3. Update only preview rect on camera event

    Script: `use_update_on_event.py`

    +------+--------+--------+
    |Cycles|FPS OSX |FPS RPi3|
    +------+--------+--------+
    |20    |94.34   |        |
    |200   |90.91   |        |
    +------+--------+--------+

4. Update only preview rect on camera event using dirty concept

    Script: `use_update_dirty_on_event.py`

    +------+--------+--------+
    |Cycles|FPS OSX |FPS RPi3|
    +------+--------+--------+
    |20    |97.09   |        |
    |200   |91.74   |        |
    +------+--------+--------+