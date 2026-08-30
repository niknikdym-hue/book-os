import json
import os
from pathlib import Path
import socket
import uvicorn
from .app import create_app


class ReadyServer(uvicorn.Server):
    def __init__(self, config: uvicorn.Config, port: int) -> None:
        super().__init__(config)
        self._ready_port = port

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        await super().startup(sockets=sockets)
        print(json.dumps({"port": self._ready_port}), flush=True)


def main() -> None:
    token = os.environ.get("BOOK_OS_SESSION_TOKEN")
    if not token:
        raise SystemExit("BOOK_OS_SESSION_TOKEN is required")
    raw_data_dir = os.environ.get("BOOK_OS_DATA_DIR")
    if not raw_data_dir:
        raise SystemExit("BOOK_OS_DATA_DIR is required")
    data_dir = Path(raw_data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    server = ReadyServer(
        uvicorn.Config(create_app(token, data_dir), access_log=False, log_level="warning"),
        listener.getsockname()[1],
    )
    server.run(sockets=[listener])


if __name__ == "__main__":
    main()
