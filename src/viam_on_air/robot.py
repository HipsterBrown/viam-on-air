import asyncio
import contextlib
from typing import Tuple

from viam.robot.client import RobotClient
from viam.components.board import Board
from viam.logging import getLogger


async def connect(api_key: str, api_key_id: str, robot_address: str):
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id,
    )
    return await RobotClient.at_address(robot_address, opts)


@contextlib.asynccontextmanager
async def create_robot(
    api_key: str, api_key_id: str, robot_address: str, board_name: str, rgb_pins: Tuple[str, str, str]
):
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id,
    )
    client = await RobotClient.at_address(robot_address, opts)
    board = Board.from_robot(client, board_name)

    robot = Robot(board=board, rgb_pins=rgb_pins)
    await robot.setup()
    try:
        yield robot
    finally:
        await robot.close()
        await client.close()


class Robot:
    def __init__(self, board: Board, rgb_pins: Tuple[str, str, str]):
        self._board = board
        self._rgb_pins = rgb_pins
        self.logger = getLogger(__name__)

    async def setup(self):
        self._pins = await asyncio.gather(
            # red, green, blue
            *[self._board.gpio_pin_by_name(pin_name) for pin_name in self._rgb_pins]
        )
        await asyncio.gather(*[pin.set_pwm_frequency(3000) for pin in self._pins])

    async def set_color(self, color: Tuple[float, float, float]):
        # (red, green, blue) = color
        await asyncio.gather(*[pin.set_pwm(color[idx]) for idx, pin in enumerate(self._pins)])

    async def blink(self, color: Tuple[float, float, float], duration: float = 5, freq: float = 0.25):
        count = duration / freq
        current = 0
        is_on = True
        while current <= count:
            current += 1
            await self.set_color(color if is_on else (1, 1, 1))
            is_on = not is_on
            await asyncio.sleep(freq)
        await self.set_color((1, 1, 1))

    async def close(self):
        await self.set_color((1, 1, 1))
