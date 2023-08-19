from fastapi import APIRouter, Request

from fast_app import templates
from services.settings import settings


main_router = APIRouter()


@main_router.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(
        "base.html", {"request": request, "path": settings.DATA_PATH}
    )
