import os
import time
from mimetypes import guess_type
from pathlib import Path
from random import randint
from typing import Annotated

from fast_app import templates
from fastapi import APIRouter, Form, HTTPException, Request, Response, UploadFile
from settings import settings
from starlette.responses import RedirectResponse
from utils import PREVIEW_CACHE_PATH, get_file_preview


tiles_router = APIRouter()
data_path = Path(settings.DATA_PATH)

_EXCLUDE_NAMES = frozenset({
    "System Volume Information"
})


def _get_path(file_path: str | None) -> Path:
    path = data_path
    if file_path:
        path = data_path / file_path
        if not path.exists():
            raise HTTPException(status_code=404, detail="Item not found")

    return path


def _get_url(method: str, path_key: str | None = None) -> str:
    if path_key:
        return tiles_router.url_path_for(method, path_key=path_key)

    return tiles_router.url_path_for(method)


def _clear_preview_cache():
    if randint(0, 20) == 1:
        for file in os.listdir(PREVIEW_CACHE_PATH):
            file_path = os.path.join(PREVIEW_CACHE_PATH, file)
            if os.path.getmtime(file_path) < time.time() - 3 * 24 * 3600:
                os.remove(file_path)


@tiles_router.get("/")
@tiles_router.get("/storage/{path_key:path}")
def tiles(request: Request, path_key: str | None = None):
    _clear_preview_cache()

    path = _get_path(path_key)
    if path.is_file():
        content_type, _ = guess_type(path.name)
        return Response(path.read_bytes(), media_type=content_type)

    data = []
    sorted_dir = sorted(path.iterdir(), key=os.path.getmtime, reverse=True)
    for item in sorted(sorted_dir, key=lambda x: x.is_file()):
        if not (item.name.startswith('.') or item.name in _EXCLUDE_NAMES):
            item_path = str(item).replace(settings.DATA_PATH, '')
            if item_path.startswith('/'):
                item_path = item_path[1:]
            data.append(dict(
                name=item.name[:50],
                img_url=get_file_preview(item),
                url=_get_url('tiles', path_key=item_path)
            ))

    return templates.TemplateResponse("plates.html", dict(
        request=request,
        data=data,
        url_new_folder=_get_url('create_folder', path_key=path_key),
        url_add_files=_get_url('add_files', path_key=path_key)
    ))


@tiles_router.post('/create-folder')
@tiles_router.post('/create-folder/{path_key:path}')
def create_folder(
    name: Annotated[str, Form(min_length=1, max_length=100, pattern=r'[A-Za-z0-9_\- ]')],
    path_key: str | None = None
):
    path = _get_path(path_key)
    path = path / name
    path.mkdir(exist_ok=True)

    return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)


@tiles_router.post('/add-files')
@tiles_router.post('/add-files/{path_key:path}')
def add_files(files: list[UploadFile], path_key: str | None = None):
    path = _get_path(path_key)

    for up_f in files:
        f_path = path / up_f.filename
        with open(f_path, 'wb') as f:
            f.write(up_f.file.read())

    return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)
