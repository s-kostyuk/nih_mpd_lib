import asyncio
import logging


LOGGER = logging.getLogger(__name__)


class MPDClient:
    """
    Simple async MPD client

    Work in progress: first draft

    MPD protocol documentation: https://www.musicpd.org/doc/protocol/
    """
    def __init__(self, host: str, port: int=6600, loop=None):
        self._host = host  # type: str
        self._port = port  # type: int

        self._loop = loop

        self._reader = None  # type: asyncio.StreamReader
        self._writer = None  # type: asyncio.StreamWriter

        self._status = None  # FIXME: specify type

        self._socket_write_lock = asyncio.Lock(loop=self._loop)

        self._idling_enabled = False
        self._idling = False

    @property
    def status(self):
        return self._status

    async def connect(self):
        LOGGER.debug("Establishing connection: %s, %s", self._host, self._port)

        self._reader, self._writer = await asyncio.open_connection(
            host=self._host, port=self._port, loop=self._loop
        )

        data = await self._read_data()

        if data.startswith(b"OK"):
            LOGGER.debug("Established, server answer: %s", data)
        else:
            raise Exception("Failed to establish connection")  # FIXME: choose proper exception type

    @staticmethod
    def _prepare_command(command: str) -> bytes:
        terminated_command = "{0}\n".format(command)

        return terminated_command.encode(encoding='utf-8')

    def _send_command(self, command: str):
        assert self._writer is not None

        self._writer.write(
            self._prepare_command(command)
        )

    async def _read_data(self):
        assert self._reader is not None

        # return await self._reader.read()  # hangs here
        return await self._reader.read(asyncio.streams._DEFAULT_LIMIT)  # works as expected, but is doubtful

    async def send_command(self, command: str):
        async with self._socket_write_lock:
            await self._exit_idle()

            LOGGER.debug("Sending command {0}... ".format(command))
            self._send_command(command)

            LOGGER.debug("Reading data...")

            data = await self._read_data()

            LOGGER.debug("Reading finished")

            await self._enter_idle()

        if data.startswith(b"ACK"):
            raise Exception("Failed to execute command")  # FIXME: choose proper Exception type
        else:
            assert data.endswith(b'OK\n')

        return data

    async def _enter_idle(self):  # FIXME: consider using of context manager
        if self._idling_enabled:
            self._idling = True

            async with self._socket_write_lock:
                self._send_command("idle")

    async def _exit_idle(self):  # FIXME: consider using of context manager
        if self._idling:
            self._idling = False

            async with self._socket_write_lock:
                self._send_command("noidle")

    async def _status_updater(self):
        # FIXME: rewrite this function
        self._idling_enabled = True

        while True:
            self._enter_idle()

            data = await self._read_data()

            # FIXME: add data checking

            # idle exited here
            self._idling = False

            self._update_status()

        # FIXME: Unreachable code
        self._idling_enabled = False

    async def _request_status(self):
        return await self.send_command("status")

    async def _update_status(self):
        self._status = await self._request_status()
