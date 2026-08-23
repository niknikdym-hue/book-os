import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException, status
from . import __version__


def create_app(token: str | None = None) -> FastAPI:
    expected = token or os.environ.get("BOOK_OS_SESSION_TOKEN")
    if not expected:
        raise RuntimeError("BOOK_OS_SESSION_TOKEN is required")
    app = FastAPI(title="BOOK OS Local Core", docs_url=None, redoc_url=None, openapi_url=None)

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if (
            authorization is None
            or not authorization.startswith("Bearer ")
            or not hmac.compare_digest(authorization[7:], expected)
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    @app.get("/health")
    def health(_: None = Depends(require_token)) -> dict[str, str]:
        return {"status": "healthy", "version": __version__}

    return app
