import os.path
from pathlib import Path

from preview_generator.exception import UnsupportedMimeType
from preview_generator.manager import PreviewManager

from fast_app import app, static_dir

PREVIEW_CACHE_PATH = os.path.join(
    os.path.dirname(__file__), 'static', '.preview_cache')

manager = PreviewManager(PREVIEW_CACHE_PATH, create_folder=True)


def get_file_preview(path: Path) -> str:
    if path.is_file():
        try:
            file_path = manager.get_jpeg_preview(str(path))
            file_path = file_path.replace(os.path.abspath(static_dir.directory), '')
        except (UnsupportedMimeType, Exception):
            file_path = '/icons/file-icon.png'
    else:
        file_path = '/icons/folder-icon.png'

    return app.url_path_for('static', path=file_path)
