from collections.abc import Mapping
import hmac
import hashlib
from typing import Any, Literal
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.background import BackgroundTask
from viam.logging import getLogger

from viam_on_air.robot import Robot

LOGGER = getLogger(__name__)


class ZoomHandler:
    _body: Mapping[str, Any] | None = None

    def __init__(self, request: Request, zoom_token: str, zoom_username: str) -> None:
        self._request = request
        self._robot: Robot = request.state.robot
        self._zoom_token = zoom_token
        self._username = zoom_username

    async def handle(self) -> Response:
        body = await self._get_body()
        event: Literal[
            "endpoint.url_validation",
            "meeting.started",
            "meeting.ended",
            "meeting.participant_joined",
            "meeting.participant_left",
        ] = body["event"]

        if event == "endpoint.url_validation":
            return self.validate_endpoint()
        if event == "meeting.participant_joined":
            return await self.welcome_participant()
        if event == "meeting.started":
            return await self.inform_participant()
        if event == "meeting.participant_left":
            return await self.dismiss_participant()
        if event == "meeting.ended":
            return await self.dismiss_meeting()
        return JSONResponse({"message": f"Event type {event} unknown"}, status_code=404)

    def validate_endpoint(self):
        assert self._body is not None

        plain_token = self._body["payload"]["plainToken"].encode()
        zoom_token = self._zoom_token.encode()
        encrypted_token = hmac.new(zoom_token, plain_token, hashlib.sha256).hexdigest()
        return JSONResponse({"plainToken": plain_token.decode(), "encryptedToken": encrypted_token})

    async def welcome_participant(self):
        participant = self._get_participant()
        if participant["user_name"] != self._username:
            return JSONResponse({})

        LOGGER.info(f"Welcome {participant['user_name']}!")
        task = BackgroundTask(self._robot.set_color, color=(1.0, 0.0, 1.0))
        return JSONResponse({}, background=task)

    async def dismiss_participant(self):
        participant = self._get_participant()
        if participant["user_name"] != self._username:
            return JSONResponse({})

        LOGGER.info(f"Goodbye {participant['user_name']}!")
        task = BackgroundTask(self._robot.set_color, color=(0.0, 1.0, 0.0))
        return JSONResponse({}, background=task)

    async def inform_participant(self):
        meeting = self._get_meeting()
        LOGGER.info(f"Meeting {meeting['topic']} has started!")
        task = BackgroundTask(self._robot.set_color, color=(0.0, 1.0, 1.0))
        return JSONResponse({}, background=task)

    async def dismiss_meeting(self):
        meeting = self._get_meeting()
        LOGGER.info(f"Meeting {meeting['topic']} has ended!")
        task = BackgroundTask(self._robot.blink, color=(0.0, 1.0, 1.0))
        return JSONResponse({}, background=task)

    async def _get_body(self):
        if self._body is None:
            self._body = await self._request.json()

        return self._body

    def _get_participant(self):
        assert self._body is not None

        return self._body["payload"]["object"]["participant"]

    def _get_meeting(self):
        assert self._body is not None

        return self._body["payload"]["object"]
