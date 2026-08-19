import asyncio
from typing import Dict, Any, Callable, Awaitable

# Общее хранилище альбомов - переиспользуется любым сценарием, где нужно
# принимать фото/видео (регистрация, редактирование анкеты и т.д.).
# Коллизий по media_group_id между разными сценариями не бывает - Telegram
# генерирует уникальный id для каждого нового альбома.
media_albums: Dict[str, Dict[str, Any]] = {}

ALBUM_WAIT_TIME = 1.0


def get_or_create_album(media_group_id: str, message) -> Dict[str, Any]:
    album = media_albums.get(media_group_id)
    if album is None:
        album = {"photos": [], "videos": [], "message": message, "task": None}
        media_albums[media_group_id] = album
    return album


def schedule_album_finalize(media_group_id: str, album: Dict[str, Any], on_finalize: Callable[..., Awaitable[None]], *args):
    """on_finalize вызывается после того, как альбом полностью собран.
    Получает (photos, videos, message, *args) - сам решает, что делать
    дальше (проверки смешивания/лимитов специфичны для каждого сценария
    и сюда не входят - это ответственность on_finalize)."""
    if album["task"]:
        album["task"].cancel()
    album["task"] = asyncio.create_task(_finalize(media_group_id, on_finalize, args))


async def _finalize(media_group_id: str, on_finalize, args):
    await asyncio.sleep(ALBUM_WAIT_TIME)

    album = media_albums.pop(media_group_id, None)
    if not album:
        return

    await on_finalize(album["photos"], album["videos"], album["message"], *args)