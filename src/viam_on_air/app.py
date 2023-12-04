import contextlib
from collections.abc import AsyncIterator, Mapping
from typing import TypedDict
from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from .zoom_handler import ZoomHandler
from .robot import create_robot, Robot

app_config = Config(".env")

ZOOM_SECRET_TOKEN = app_config("ZOOM_SECRET_TOKEN", cast=Secret)
ZOOM_USERNAME = app_config("ZOOM_USERNAME", cast=str)
VIAM_API_KEY = app_config("VIAM_API_KEY", cast=Secret)
VIAM_API_KEY_ID = app_config("VIAM_API_KEY_ID", cast=Secret)
VIAM_ADDRESS = app_config("VIAM_ADDRESS", cast=str)
BOARD_NAME = app_config("BOARD_NAME", cast=str, default="board")
RGB_PINS = app_config("RGB_PINS", cast=CommaSeparatedStrings, default=["18", "5", "19"])


class State(TypedDict):
    robot: Robot


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette) -> AsyncIterator[State]:
    async with create_robot(
        api_key=str(VIAM_API_KEY),
        api_key_id=str(VIAM_API_KEY_ID),
        robot_address=VIAM_ADDRESS,
        board_name=BOARD_NAME,
        rgb_pins=tuple(RGB_PINS),
    ) as robot:
        yield {"robot": robot}


async def homepage(request: Request):
    return JSONResponse({"message": "Ok"})


async def zoom(request: Request):
    handler = ZoomHandler(request=request, zoom_token=str(ZOOM_SECRET_TOKEN), zoom_username=ZOOM_USERNAME)
    return await handler.handle()


async def not_found(request, exception):
    print("Not found")
    return PlainTextResponse(status_code=404, content="Not Found")


async def server_error(request, exception):
    print("Server error")
    return PlainTextResponse(status_code=500, content="Server Error")


routes = [Route("/", homepage), Route("/webhooks/zoom", zoom, methods=["POST"])]

exception_handlers = {404: not_found, 500: server_error}

app = Starlette(debug=True, routes=routes, exception_handlers=exception_handlers, lifespan=lifespan)
