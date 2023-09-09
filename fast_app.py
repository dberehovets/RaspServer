from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from utils import random_string


app = FastAPI(debug=True)

static_dir = StaticFiles(directory="static")
app.mount("/static", static_dir, name="static")

app.add_middleware(SessionMiddleware, secret_key=random_string())

templates = Jinja2Templates(directory="templates")


def register_routes(fast_app: FastAPI):
    from views.tiles import tiles_router

    fast_app.include_router(tiles_router)


register_routes(app)
