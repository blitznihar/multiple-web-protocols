import json
from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/hook")
async def hook(req: Request):
    body = await req.json()
    headers = dict(req.headers)
    print("=== WEBHOOK RECEIVED ===")
    print("Headers:", json.dumps(headers, indent=2))
    print("Body:", json.dumps(body, indent=2))
    return {"ok": True}
