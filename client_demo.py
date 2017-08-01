from nih_mpd_lib import MPDClient

import asyncio
import logging
# import sys

logging.basicConfig(level=logging.DEBUG)

# MPDClientLogger = logging.getLogger("nih_mpd_lib.MPDClient")
# MPDClientLogger.setLevel(logging.DEBUG)
# stdout_stream = logging.StreamHandler(sys.stdout)
# MPDClientLogger.addHandler(stdout_stream)


def pass_command_to_loop(command: str, client: MPDClient, loop: asyncio.AbstractEventLoop):
    loop.create_task(client.send_command(command))


def console_interface_function(client: MPDClient, loop: asyncio.AbstractEventLoop):
    while True:
        data = input()

        print("Hey!!!", loop, client)

        if data.startswith("exit"):
            break

        loop.call_soon_threadsafe(pass_command_to_loop, data, client, loop)

    #loop.stop()


async def execute_command(client: MPDClient, command: str):
    data = await client.send_command(command)

    print("Command executed:", data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    client = MPDClient(host="localhost", loop=loop)

    loop.run_until_complete(client.connect())

    #loop.run_until_complete(execute_command(client, "play"))

    #loop.run_until_complete(execute_command(client, "stop"))

    #loop.run_until_complete(client._update_status())  # Only for debugging

    #th = threading.Thread(target=console_interface_function, args=(loop, client), daemon=True)

    #print(client.status)

    try:
        loop.run_in_executor(None, console_interface_function, client, loop)
        loop.run_forever()
    finally:
        loop.close()
