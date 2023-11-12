import io
import time
from threading import Condition

from fast_app import templates
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from libcamera import Transform
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput


camera_router = APIRouter()


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"size": (640, 480)},
    transform=Transform(vflip=True, hflip=True)
))
output = StreamingOutput()


connects = set()


@camera_router.get("/")
async def camera_view(request: Request):
    # print(request.url_for('camera_streaming_view'))
    return templates.TemplateResponse('camera.html', dict(
        request=request,
        streaming_url=camera_router.url_path_for('camera:camera_streaming_view')
    ))


@camera_router.get("/streaming")
async def camera_streaming_view(request: Request):
    global connects
    if not connects:
        picam2.start_recording(JpegEncoder(), FileOutput(output))
    elif len(connects) >= 5:
        return 'Too many connects'

    val = time.time()
    connects.add(val)

    async def generate():
        while not await request.is_disconnected():
            with output.condition:
                output.condition.wait()
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(output.frame) + b'\r\n')

        connects.remove(val)
        if not connects:
            picam2.stop_recording()

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame")
