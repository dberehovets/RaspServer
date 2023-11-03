from picamera2 import Picamera2, CameraConfiguration
import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse


camera_router = APIRouter()


camera = Picamera2()
camera_config = camera.create_preview_configuration()
camera.configure(camera_config)


@camera_router.get("/")
def stream():

    async def generate():
        while True:
            frame = await camera.capture_frame()
            yield frame.tobytes()

    return StreamingResponse(generate())
