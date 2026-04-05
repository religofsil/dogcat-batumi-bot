import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings

router = APIRouter(tags=["debug"])


@router.post("/api/__debug/client-log")
async def client_debug_log(request: Request) -> dict[str, str]:
    settings = get_settings()
    raw = settings.client_debug_log_path
    if not raw:
        raise HTTPException(status_code=404, detail="disabled")
    path = Path(raw)
    try:
        body: dict[str, Any] = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid_json") from e
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False) + "\n")
    return {"ok": "1"}
