import numpy as np
import cv2

codec = "XVID"
ext = "avi"
out = cv2.VideoWriter(f'{ext}-{codec}.{ext}', cv2.VideoWriter_fourcc(*codec), fps, (size[1], size[0]))
for _ in range(fps * duration):
    data = np.random.randint(0, 256, (size[0], size[1], 3), dtype='uint8')
    out.write(data)
out.release()

