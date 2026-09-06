import hmac
import json
import os
from pathlib import Path
import socket

from fastapi import Header, HTTPException, status
import uvicorn

from .app import create_app
from .launch_api import build_launch_router
from .model_gateway import ModelGateway
from .provider_adapters import BookOSOpenAIResponsesAdapter, YandexChatCompletionsAdapter
from .secrets import MacOSKeychainSecretStore


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

    secret_store = MacOSKeychainSecretStore()
    gateway = ModelGateway(
        {
            "openai": BookOSOpenAIResponsesAdapter(secret_store),
            "yandex": YandexChatCompletionsAdapter(secret_store),
        }
    )
    app = create_app(token, data_dir, gateway=gateway)

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if (
            authorization is None
            or not authorization.startswith("Bearer ")
            or not hmac.compare_digest(authorization[7:], token)
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    app.include_router(build_launch_router(data_dir, require_token, gateway))

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    server = ReadyServer(
        uvicorn.Config(
            app,
            access_log=False,
            log_level="warning",
            loop="asyncio",
            http="h11",
            lifespan="off",
        ),
        listener.getsockname()[1],
    )
    server.run(sockets=[listener])


if __name__ == "__main__":
    main()
