import picamera
from fastapi import FastAPI
from starlette.responses import StreamingResponse


class Camera:
    def __init__(self):
        self.camera = picamera.PiCamera()

    def read(self):
        return self.camera.capture(format="jpeg")


app = FastAPI()


@app.get("/stream", response_class=StreamingResponse)
async def stream():
    camera = Camera()

    while True:
        frame = await camera.read()

        yield frame
