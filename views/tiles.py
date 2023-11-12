import os
import re
import shutil
import time
from mimetypes import guess_type
from pathlib import Path
from random import randint
from typing import Annotated

import magic
from fast_app import templates
from fastapi import APIRouter, Form, HTTPException, Request, Response, UploadFile
from fastapi.params import Header
from pydantic import BaseModel, conlist, constr, field_validator
from settings import settings
from starlette.responses import RedirectResponse

from utils import PREVIEW_CACHE_PATH, Flash, get_file_preview


tiles_router = APIRouter()
data_path = Path(settings.DATA_PATH)

_EXCLUDE_NAMES = frozenset({
    "System Volume Information"
})
_VIDEO_CHUNK_SIZE = 69861375


class DeleteModel(BaseModel):
    paths: conlist(constr(min_length=1, max_length=500), min_length=1)

    @field_validator('paths')
    def validate_paths(cls, val: list[str]) -> list[str]:
        for p in val:
            if not _get_full_path(p):
                raise ValueError(f"File of path '{p}' not found.")
        return val


class RenameModel(BaseModel):
    path: constr(min_length=1, max_length=500)
    new_name: constr(min_length=3, max_length=100)

    @field_validator('path')
    def validate_path(cls, val: str) -> str:
        if not _get_full_path(val):
            raise ValueError(f"File of path '{val}' not found.")
        return val

    @field_validator('new_name')
    def validate_new_name(cls, val: str) -> str:
        if not re.match(r'[A-Za-z0-9_\- ]', val):
            raise ValueError(f"Name contains not allowed symbols. Use A-Z, a-z, 0-9, - and space")
        return val


def _get_full_path(file_path: str | None) -> Path | None:
    path = data_path
    if file_path:
        path = data_path / file_path
        if not path.exists():
            return

    return path


def _get_url(method: str, path_key: str | None = None) -> str:
    if path_key:
        return tiles_router.url_path_for(method, path_key=path_key)

    return tiles_router.url_path_for(method)


def _get_breadcrumb(path_key: str | None = None) -> list[dict]:
    if path_key is None:
        return []

    result = [dict(name='Home', url=_get_url('tiles'))]
    names = path_key.split('/')
    names_len = len(names)
    for idx in range(names_len):
        sublist = names[:idx + 1]
        result.append(dict(
            name=sublist[-1],
            url=_get_url('tiles', path_key='/'.join(sublist)) if idx + 1 < names_len else None
        ))

    return result


def _clear_preview_cache():
    if randint(0, 20) == 1:
        for file in os.listdir(PREVIEW_CACHE_PATH):
            file_path = os.path.join(PREVIEW_CACHE_PATH, file)
            if os.path.getmtime(file_path) < time.time() - 3 * 24 * 3600:
                os.remove(file_path)


def _is_file_video(item: Path):
    return item.is_file() and magic.from_file(item, mime=True).startswith('video')


def _get_video_source(request: Request, item: Path, path_key: str) -> str | None:
    if _is_file_video(item):
        return str(request.url_for('tiles:video_source', path_key=path_key))


@tiles_router.get("/")
@tiles_router.get("/storage/{path_key:path}")
async def tiles(request: Request, path_key: str | None = None):
    _clear_preview_cache()

    path = _get_full_path(path_key)
    if not path:
        raise HTTPException(status_code=404, detail="Item not found")

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
                path_key=item_path,
                name=item.name[:50],
                img_url=get_file_preview(item),
                url=_get_url('tiles', path_key=item_path),
                video_source=_get_video_source(request, item, item_path)
            ))

    return templates.TemplateResponse("plates.html", dict(
        request=request,
        data=data,
        breadcrumb=_get_breadcrumb(path_key),
        url_new_folder=_get_url('create_folder', path_key=path_key),
        url_add_files=_get_url('add_files', path_key=path_key),
        url_delete_items=_get_url('delete_items'),
        url_rename_item=_get_url('rename_item'),
    ))


@tiles_router.post('/create-folder')
@tiles_router.post('/create-folder/{path_key:path}')
async def create_folder(
    request: Request,
    name: Annotated[str, Form(min_length=1, max_length=100, pattern=r'[A-Za-z0-9_\- ]')],
    path_key: str | None = None
):
    path = _get_full_path(path_key)
    if not path:
        Flash.error(request, 'Path not found')
        return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)

    path = path / name
    path.mkdir(exist_ok=True)

    return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)


@tiles_router.post('/add-files')
@tiles_router.post('/add-files/{path_key:path}')
async def add_files(request: Request, files: list[UploadFile], path_key: str | None = None):
    path = _get_full_path(path_key)
    if not path:
        Flash.error(request, 'Path not found')
        return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)

    for up_f in files:
        f_path = path / up_f.filename
        with open(f_path, 'wb') as f:
            f.write(up_f.file.read())

    return RedirectResponse(_get_url('tiles', path_key=path_key), status_code=302)


@tiles_router.post('/delete-items')
async def delete_items(data: DeleteModel):
    for p in data.paths:
        path = _get_full_path(p)
        if path.is_file():
            try:
                os.remove(path)
            except OSError as err:
                return {"status": "error", "detail": str(err)}
        else:
            shutil.rmtree(path)

    return {"status": "ok", "detail": "Successfully removed"}


@tiles_router.post('/rename-item')
async def rename_item(data: RenameModel):
    item = _get_full_path(data.path)
    new_name = data.new_name
    if item.is_file():
        f_type = item.name.rsplit('.', 1)[-1]
        if f_type != new_name.rsplit('.', 1)[-1]:
            new_name += f'.{f_type}'

    new_path = Path(str(item).replace(item.name, new_name))

    item.rename(new_path)

    return {"status": "ok"}


@tiles_router.get('/video-source/{path_key:path}')
async def video_source(path_key: str, range: str | None = Header(None)):
    item = _get_full_path(path_key)
    if not (item and item.is_file() and _is_file_video(item)):
        raise HTTPException(status_code=404, detail="Item not found")

    if range is None:
        return Response(open(item, "rb").read(), status_code=200)

    file_size = item.stat().st_size
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else min(start + _VIDEO_CHUNK_SIZE, file_size - 1)

    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Range': f'bytes {str(start)}-{str(end)}/{file_size}'
    }

    with open(item, "rb") as video:
        video.seek(start)
        data = video.read(end - start + 1)

    return Response(data, headers=headers, status_code=206)
