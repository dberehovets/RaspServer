import json
import os.path
import random
from pathlib import Path
from string import ascii_lowercase, digits

from fastapi import Request
from preview_generator.exception import UnsupportedMimeType
from preview_generator.manager import PreviewManager


PREVIEW_CACHE_PATH = os.path.join(
    os.path.dirname(__file__), 'static', '.preview_cache')

manager = PreviewManager(PREVIEW_CACHE_PATH, create_folder=True)


def get_file_preview(path: Path) -> str:
    from fast_app import app, static_dir

    if path.is_file():
        try:
            file_path = manager.get_jpeg_preview(str(path))
            file_path = file_path.replace(os.path.abspath(static_dir.directory), '')
        except (UnsupportedMimeType, Exception):
            file_path = '/icons/file-icon.png'
    else:
        file_path = '/icons/folder-icon.png'

    return app.url_path_for('static', path=file_path)


def random_string(prefix: str = '', length: int = 10) -> str:
    symbols = ascii_lowercase + digits
    rand_str = u''.join(random.choice(symbols) for _ in range(length))
    return u'%s%s' % (prefix or '', rand_str)


class Flash:
    @staticmethod
    def error(request: Request, message: str):
        if msgs := request.session.get('messages'):
            msgs.append(dict(message=message, type='danger'))
            request.session['messages'] = list(map(json.loads, set(map(json.dumps, msgs))))
        else:
            request.session['messages'] = [dict(message=message, type='danger')]

        print('saved', (request.session['messages'],))
