from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from utils import random_string


app = FastAPI(debug=True)


@app.on_event("shutdown")
async def on_shutdown():
    from views.camera import picam2

    picam2.stop_recording()

static_dir = StaticFiles(directory="static")
app.mount("/static", static_dir, name="static")

app.add_middleware(SessionMiddleware, secret_key=random_string())

templates = Jinja2Templates(directory="templates")


def register_routes(fast_app: FastAPI):
    from views.camera import camera_router
    from views.tiles import tiles_router

    fast_app.mount('/', app=tiles_router, name='tiles')
    fast_app.mount('/camera', app=camera_router, name='camera')


register_routes(app)
