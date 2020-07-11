from typing import Tuple
import logging

logger = logging.getLogger("tools.logger_example.server")


class AbstractServer:
    def __init__(self, *args, **kwargs):
       raise NotImplementedError

    async def _handle_connection(self, *args, **kwargs):
        raise NotImplementedError

    async def _handle_request(self, *args, **kwargs):
        raise NotImplementedError

    async def _send_file(self, *args, **kwargs):
        raise NotImplementedError

    async def _receive_file(self, *args, **kwargs):
        raise NotImplementedError

