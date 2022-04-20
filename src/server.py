import os
from collections import namedtuple
from datetime import datetime
from pathlib import Path

from aiohttp import web


def Time(hour: int, minute: int):
    return hour * 60 + minute


Interval = namedtuple('Interval', ['start', 'end'])
Option = namedtuple('Option', ['interval', 'filename'])

BASE_DIR = Path(os.environ.get('BASE_DIR', r'./data'))
HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', 8000))

IMAGE_MAP = {
    'cityscape1': [
        Option(Interval(start=Time(hour=0, minute=0), end=Time(hour=5, minute=59)), BASE_DIR / 'cityscape1' / 'night.jpeg'),
        Option(Interval(start=Time(hour=6, minute=0), end=Time(hour=11, minute=59)), BASE_DIR / 'cityscape1' / 'morning.jpeg'),
        Option(Interval(start=Time(hour=12, minute=0), end=Time(hour=17, minute=59)), BASE_DIR / 'cityscape1' / 'afternoon.png'),
        Option(Interval(start=Time(hour=18, minute=0), end=Time(hour=23, minute=59)), BASE_DIR / 'cityscape1' / 'evening.png'),
    ],
}


def get_filename(name: str):
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    for option in IMAGE_MAP.get(name, []):
        if option.interval.start <= now_minutes <= option.interval.end:
            return option.filename


class Server:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_get('/notion/dynamic_images/{name}', self.notion_images_handler)

    def run(self, host: str, port: int):
        web.run_app(self.app, host=host, port=port)

    def response_error(self, exception: Exception, status=500):
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
