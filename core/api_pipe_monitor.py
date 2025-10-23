from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json

app = FastAPI()

# Allow frontend to call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def get_ttl_status(ttl, expected=None):
    if ttl == -2:
        return {"icon": "💀", "status": "missing"}
    if ttl == -1:
        return {"icon": "🩵", "status": "persistent"}
    if ttl <= 5:
        return {"icon": "🔴", "status": f"{ttl}s"}
    if ttl <= 10:
        return {"icon": "🟡", "status": f"{ttl}s"}
    return {"icon": "🟢", "status": f"{ttl}s"}

@app.get("/api/pipes")
def get_pipes():
    patterns = {
        "Integration": "meta:*",
        "Heartbeat": "heartbeat:*",
        "Mesh": "mesh:*",
        "ChainFeed Feeds": "chainfeed:*",
        "Feed Health": "feed:*",
    }
    data = {}
    for category, pattern in patterns.items():
        keys = r.keys(pattern)
        data[category] = []
        for key in keys:
            ttl = r.ttl(key)
            status = get_ttl_status(ttl)
            data[category].append({
                "name": key,
                "ttl": ttl,
                "status": status["status"],
                "icon": status["icon"]
            })
    return {"categories": data}