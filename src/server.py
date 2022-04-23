import os
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from aiohttp import web

BASE_DIR = Path(os.environ.get('BASE_DIR', r'./data'))
HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', 8000))


def time24(hour: int, minute: int):
    if 0 <= hour < 24 and 0 <= minute < 60:
        return hour * 60 + minute
    raise TypeError


class HalfInterval:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __contains__(self, time: int):
        if self.start < self.end:
            return self.start <= time < self.end
        else:
            full = 24 * 60
            return self.start <= time < self.end + full or self.start - full <= time < self.end


Option = namedtuple('Option', ['interval', 'filename'])

INTERVALS = {
    'morning': HalfInterval(start=time24(hour=4, minute=0), end=time24(hour=10, minute=0)),
    'afternoon': HalfInterval(start=time24(hour=10, minute=0), end=time24(hour=16, minute=0)),
    'evening': HalfInterval(start=time24(hour=16, minute=0), end=time24(hour=22, minute=0)),
    'night': HalfInterval(start=time24(hour=22, minute=0), end=time24(hour=4, minute=0)),
}

IMAGE_MAP = {
    'cityscape1.png': [
        Option(INTERVALS['night'], BASE_DIR / 'cityscape1' / 'night.jpeg'),
        Option(INTERVALS['morning'], BASE_DIR / 'cityscape1' / 'morning.jpeg'),
        Option(INTERVALS['afternoon'], BASE_DIR / 'cityscape1' / 'afternoon.png'),
        Option(INTERVALS['evening'], BASE_DIR / 'cityscape1' / 'evening.png'),
    ],
    'cityscape2.png': [
        Option(INTERVALS['night'], BASE_DIR / 'cityscape2' / 'night.jpg'),
        Option(INTERVALS['morning'], BASE_DIR / 'cityscape2' / 'morning.jpg'),
        Option(INTERVALS['afternoon'], BASE_DIR / 'cityscape2' / 'afternoon.jpg'),
        Option(INTERVALS['evening'], BASE_DIR / 'cityscape2' / 'evening.jpg'),
    ],
    'bg.png': [
        Option(INTERVALS['night'], BASE_DIR / 'bg' / 'night.png'),
        Option(INTERVALS['morning'], BASE_DIR / 'bg' / 'morning.jpg'),
        Option(INTERVALS['afternoon'], BASE_DIR / 'bg' / 'afternoon.png'),
        Option(INTERVALS['evening'], BASE_DIR / 'bg' / 'evening.png'),
    ],
}


def get_filename(name: str):
    now = datetime.now(tz=ZoneInfo("Europe/Moscow"))
    now_minutes = time24(hour=now.hour, minute=now.minute)
    for option in IMAGE_MAP.get(name, []):
        if now_minutes in option.interval:
            print(now, option.filename)
            return option.filename


class Server:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_get('/notion/dynamic_images/{name}', self.notion_images_handler)

    def run(self, host: str, port: int):
        web.run_app(self.app, host=host, port=port)

    @staticmethod
    def response_error(exception: Exception, status=500):
        return web.json_response({
            'type': "Internal Server Error",
            'error': f'{exception.__class__.__name__}: {exception}',
        }, status=status)

    async def notion_images_handler(self, request: web.Request):
        filename = get_filename(request.match_info.get('name', None))

        if not filename:
            return self.response_error(IOError("Not found"), 404)

        try:
            file = open(filename, 'rb')
        except IOError as e:
            return self.response_error(e)

        data = file.read()
        file.close()

        return web.Response(body=data, content_type="image/" + filename.suffix.lower()[1:])


def main():
    s = Server()
    s.run(HOST, PORT)


if __name__ == "__main__":
    main()
