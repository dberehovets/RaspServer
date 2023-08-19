from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def register_routes(fast_app: FastAPI):
    from views.main_page import main_router

    fast_app.include_router(main_router)


register_routes(app)
