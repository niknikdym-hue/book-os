import json
import os
import socket
import uvicorn
from .app import create_app


def main() -> None:
    token = os.environ.get("BOOK_OS_SESSION_TOKEN")
    if not token:
        raise SystemExit("BOOK_OS_SESSION_TOKEN is required")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    print(json.dumps({"port": listener.getsockname()[1]}), flush=True)
    uvicorn.Server(uvicorn.Config(create_app(token), access_log=False, log_level="warning")).run(
        sockets=[listener]
    )


if __name__ == "__main__":
    main()
