import os
import time
import uuid

import jwt
from fastapi import FastAPI, HTTPException, Request

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-nf659zb8.apps.exam.local"

PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n")

# Vercel Python entry point: must be at module level.
app = FastAPI(title="OAuth 2.0 / OIDC Token Verification Service")


@app.middleware("http")
async def add_request_headers(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)

    elapsed = max(0.0, time.perf_counter() - start)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


@app.get("/")
async def root():
    return {"status": "ok", "endpoint": "/verify"}


@app.post("/verify")
async def verify_token(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"valid": False, "error": "invalid_json"},
        )

    token = body.get("token") if isinstance(body, dict) else None

    if not isinstance(token, str) or not token.strip():
        raise HTTPException(
            status_code=400,
            detail={"valid": False, "error": "missing_token"},
        )

    if not PUBLIC_KEY.strip():
        raise HTTPException(
            status_code=500,
            detail="JWT_PUBLIC_KEY is not configured",
        )

    try:
        claims = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["exp", "iss", "aud", "sub"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )

        return {
            "valid": True,
            "email": claims.get("email", ""),
            "sub": claims["sub"],
            "aud": claims["aud"],
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"valid": False, "error": "expired"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=401,
            detail={"valid": False, "error": "invalid_audience"},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=401,
            detail={"valid": False, "error": "invalid_issuer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={"valid": False, "error": "invalid_token"},
        )
