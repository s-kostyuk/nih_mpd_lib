from nih_mpd_lib import MPDClient

import asyncio
import logging
# import sys

logging.basicConfig(level=logging.DEBUG)

# MPDClientLogger = logging.getLogger("nih_mpd_lib.MPDClient")
# MPDClientLogger.setLevel(logging.DEBUG)
# stdout_stream = logging.StreamHandler(sys.stdout)
# MPDClientLogger.addHandler(stdout_stream)


async def execute_command(client: MPDClient, command: str):
    data = await client.send_command(command)

    print("Command executed:", data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    client = MPDClient(host="localhost", loop=loop)

    loop.run_until_complete(client.connect())

    loop.run_until_complete(execute_command(client, "play"))

    loop.run_until_complete(execute_command(client, "stop"))

    try:
        loop.run_forever()
    finally:
        loop.close()
