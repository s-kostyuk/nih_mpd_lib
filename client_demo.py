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
    """
    Utility function that calls specified command on MPD Client
    in specified EventLoop
    :param command: command to be called
    :param client: an instance of MPDClient
    :param loop: target EventLoop
    :return: None
    """
    loop.create_task(client.send_command(command))


def console_interface_function(client: MPDClient, loop: asyncio.AbstractEventLoop):
    """
    Simple BLOCKING function with an infinite loop inside that read commands from stdin
    and pass them to the specified instance of MPDClient
    :param client: an instance of MPDClient
    :param loop: target EventLoop
    :return: None
    """
    while True:
        data = input()  # get another command from user

        print("Hey!!!", loop, client)  # notify user that the command was read, for debugging

        if data == "exit":  # exit from infinite loop on command == "exit"
            print("Input loop interrupted")
            break

        loop.call_soon_threadsafe(pass_command_to_loop, data, client, loop)

    loop.stop()  # Stop event loop and exit from the program


async def execute_command(client: MPDClient, command: str):
    """
    Utility function that executes specified command on MPDClient and then
    prints returned value
    :param client: an instance of MPDClient
    :param command: MPD command to be called
    :return: None
    """
    data = await client.send_command(command)

    print("Command executed:", data)


if __name__ == "__main__":
    """
    Main activity goes here
    """
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    client = MPDClient(host="localhost", loop=loop)  # Create an instance of MPDClient

    loop.run_until_complete(client.connect())  # Initialize connection

    #loop.run_until_complete(execute_command(client, "play"))

    #loop.run_until_complete(execute_command(client, "stop"))

    #loop.run_until_complete(client._update_status())  # Only for debugging

    #th = threading.Thread(target=console_interface_function, args=(loop, client), daemon=True)

    # Plan on execution a status updater coroutine
    updater_task = loop.create_task(client.wait_for_updates())  # type: asyncio.Task

    #print(client.status)

    try:
        loop.run_in_executor(None, console_interface_function, client, loop)  # Run CLI in separate thread
        loop.run_forever()  # Run event loop and block further app execution (optionally)
    except KeyboardInterrupt:
        pass
    finally:
        updater_task.cancel()

        try:
            loop.run_until_complete(asyncio.gather(updater_task))
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()  # close event loop
