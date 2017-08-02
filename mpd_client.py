import asyncio
import logging

LOGGER = logging.getLogger(__name__)


class MPDClient:
    """
    Simple async MPD client

    Work in progress: first draft

    MPD protocol documentation: https://www.musicpd.org/doc/protocol/
    """
    IDLING_CANCELED = b"idling canceled\nOK\n"

    def __init__(self, host: str, port: int = 6600, loop: asyncio.AbstractEventLoop = None):
        self._host = host  # type: str
        self._port = port  # type: int

        self._loop = loop  # type: asyncio.AbstractEventLoop

        self._reader = None  # type: asyncio.StreamReader
        self._writer = None  # type: asyncio.StreamWriter

        self._status = None  # FIXME: specify type

        self._command_lock = asyncio.Lock(loop=self._loop)

        # Event that allows idling loop to start the new iteration
        self._idling_allowed = asyncio.Event(loop=self._loop)

        self._is_idling = False

    @property
    def status(self):
        """
        Get the copy of the current MPD status information
        :return: status information
        """
        return self._status

    async def connect(self):
        """
        Establish a TCP connection to MPD server
        :return: None
        """
        LOGGER.debug("Establishing connection: %s, %s", self._host, self._port)

        # Open TCP connection and get StreamReader and StreamWriter pair
        self._reader, self._writer = await asyncio.open_connection(
            host=self._host, port=self._port, loop=self._loop
        )

        data = await self._read_data()

        if data.startswith(b"OK"):
            LOGGER.debug("Established, server answer: %s", data)
        else:
            raise Exception("Failed to establish connection, server answer: %s",
                            data)  # FIXME: choose proper exception type

        self._allow_idling()

    async def send_command(self, command: str) -> bytes:
        """
        Execute general MPD command
        :param command: command to be sent
        :return: execution result; a server answer
        """
        return await self._send_command_while_idling(command)

    async def update_status(self):
        """
        Force update status
        :return: None
        """
        # Send 'status' command and save returned data to self._status
        self._status = await self._request_status()

    async def wait_for_updates(self):
        """
        An infinite loop which sends 'idle', waits for any events on
        MPD server and updates self.status on each event
        :return: None
        """
        while True:
            await self._idling_allowed.wait()

            self._is_idling = True

            data = await self._send_command_with_response("idle")

            logging.debug("Idling finished with data: %s", data)

            if data != self.IDLING_CANCELED:
                await self.update_status()

    async def _read_data(self) -> bytes:
        """
        Read all pending data from StreamReader buffer
        :return: data read
        """
        if self._writer is None:
            raise Exception(
                "Attempted to read data without an established connection!")  # FIXME: choose proper exception type

        # return await self._reader.read()  # hangs here
        return await self._reader.read(asyncio.streams._DEFAULT_LIMIT)  # works as expected, but is doubtful

    @staticmethod
    def _prepare_command(command: str) -> bytes:
        """
        Generate EOL-terminated bytestring based on general string
        :param command: string, command to be sent
        :return: bytes-encoded EOL-terminated string
        """
        terminated_command = "{0}\n".format(command)

        return terminated_command.encode(encoding='utf-8')

    async def _send_command_base(self, command: str):
        """
        Send a command to the MPD server without waiting for an answer
        :param command: command to be sent
        :return: None
        """
        if self._writer is None:
            raise Exception(
                "Attempted to send a command without an established connection!")  # FIXME: choose proper exception type

        self._writer.write(
            self._prepare_command(command)
        )

    async def _send_command_with_response(self, command: str) -> bytes:
        """
        Send a command to the MPD server and wait for an answer
        :param command: command to be sent
        :return: execution result; a server answer
        """
        async with self._command_lock:
            LOGGER.debug("Sending command {0}... ".format(command))
            await self._send_command_base(command)

            LOGGER.debug("Reading data...")

            data = await self._read_data()

            LOGGER.debug("Reading finished: %s", data)

        if data.startswith(b"ACK"):
            raise Exception("Failed to execute command")  # FIXME: choose proper Exception type
        else:
            assert data.endswith(b'OK\n')

        return data

    async def _send_command_while_idling(self, command: str) -> bytes:
        """
        Stop idling, send a command to the MPD server and wait for an answer
        :param command: command to be sent
        :return: execution result; a server answer
        """
        await self._stop_idling_if_needed()

        # Get execution result and allow idling even if command failed
        try:
            response = await self._send_command_with_response(command)
        finally:
            self._allow_idling()

        return response

    async def _stop_idling_if_needed(self):
        """
        Stop idling:
         - block idling loop; clear self._idling_allowed event
         - feed self.IDLING_CANCELED to the StreamReader buffer
         - send 'noidle' if 'idle' command was sent to MPD server
        :return: None
        """
        if self._is_idling:
            logging.debug("Sending noidle...")

            # WARNING: The order is important
            self._idling_allowed.clear()  # disallow idling first
            self._reader.feed_data(
                self.IDLING_CANCELED)  # then let wait_for_updates loop to pass reader.read() statement

            # WARNING: MPD sends an b'OK\n' response only to the first 'noidle' call.
            # If 'idle' command was already canceled, then there is no answer to 'noidle',
            # which results to infinite waiting for response and deadlock in
            # self._send_command_with_response.
            await self._send_command_with_response("noidle")

            # Reset is_idling state to prevent successive calls of 'noidle'
            self._is_idling = False

    def _allow_idling(self):
        """
        Allow idling loop to start the new iteration
        :return: None
        """
        self._idling_allowed.set()

    async def _request_status(self) -> bytes:
        """
        Send 'status' command and get its response
        :return: a response to 'status' command
        """
        return await self.send_command("status")
