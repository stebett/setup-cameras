import numpy as np
import cv2

extentions = ["mp4", "avi"]
codecs = ["XVID", "MJPG" , "DIVX", "H264"]
size = 720*16//9, 720
duration = 2
fps = 25

codec = "MJPG"
ext = "avi"
out = cv2.VideoWriter(f'{ext}-{codec}.{ext}', cv2.VideoWriter_fourcc(*codec), fps, (size[1], size[0]))
for _ in range(fps * duration):
    data = np.random.randint(0, 256, (size[0], size[1], 3), dtype='uint8')
    out.write(data)
out.release()


writer = cv2.VideoWriter("output.avi", cv2.VideoWriter_fourcc(*"MJPG"), 30,(640,480))

for frame in range(100):
    writer.write(np.random.randint(0, 255, (480,640,3)).astype('uint8'))

writer.release()
