from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates


app = FastAPI(debug=True)

static_dir = StaticFiles(directory="static")
app.mount("/static", static_dir, name="static")

templates = Jinja2Templates(directory="templates")


def register_routes(fast_app: FastAPI):
    from views.tiles import tiles_router

    fast_app.include_router(tiles_router)


register_routes(app)
