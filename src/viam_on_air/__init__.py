# SPDX-FileCopyrightText: 2023-present HipsterBrown <headhipster@hipsterbrown.com>
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dotenv

from viam.robot.client import RobotClient
from viam.components.board import Board

config = dotenv.dotenv_values(dotenv_path=".env")


async def connect():
    opts = RobotClient.Options.with_api_key(
        # Replace "<API-KEY>" (including brackets) with your robot's api key
        api_key=config.get("VIAM_API_KEY") or "",
        # Replace "<API-KEY-ID>" (including brackets) with your robot's api key id
        api_key_id=config.get("VIAM_API_KEY_ID") or "",
    )
    return await RobotClient.at_address(config.get("VIAM_ADDRESS") or "", opts)


async def main():
    robot = await connect()

    print("Resources:")
    print(robot.resource_names)

    # Note that the pin supplied is a placeholder. Please change this to a valid pin you are using.
    # board
    board = Board.from_robot(robot, "board")
    (pot1, pot2, pot3) = await asyncio.gather(
        board.analog_reader_by_name("pot1"), board.analog_reader_by_name("pot2"), board.analog_reader_by_name("pot3")
    )
    (red_pin, green_pin, blue_pin) = await asyncio.gather(
        board.gpio_pin_by_name("18"), board.gpio_pin_by_name("19"), board.gpio_pin_by_name("5")
    )
    # red_pin = await board.gpio_pin_by_name("18")
    # green_pin = await board.gpio_pin_by_name("19")
    # blue_pin = await board.gpio_pin_by_name("5")

    await asyncio.gather(
        red_pin.set_pwm_frequency(3000), green_pin.set_pwm_frequency(3000), blue_pin.set_pwm_frequency(3000)
    )
    while True:
        (red_val, green_val, blue_val) = await asyncio.gather(pot1.read(), pot2.read(), pot3.read())
        print(f"Current values: Red {red_val} | Green {green_val} | Blue {blue_val}")
        await asyncio.gather(
            red_pin.set_pwm(red_val / 3200), green_pin.set_pwm(green_val / 3200), blue_pin.set_pwm(blue_val / 3200)
        )
        await asyncio.sleep(0.5)

    # Don't forget to close the robot when you're done!
    await robot.close()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
