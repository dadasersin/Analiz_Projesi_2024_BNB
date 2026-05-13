from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import time
from datetime import datetime
from typing import Dict, List

app = FastAPI(title="Antigravity Command Center")

# CORS for Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
DEVICES: Dict[str, dict] = {}
DECISION_LOG: List[dict] = []
RENDER_URL = "https://analiz-projesi-2024-bnb.onrender.com" 

# WhatsApp Configuration (CallMeBot)
WHATSAPP_PHONE = "+90..." 
WHATSAPP_API_KEY = "YOUR_KEY"

async def send_whatsapp_notification(message: str):
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={message}&apikey={WHATSAPP_API_KEY}"
            await client.get(url)
        except: pass

def log_decision(message: str):
    log_entry = {"timestamp": datetime.now().strftime("%H:%M:%S"), "message": message}
    DECISION_LOG.insert(0, log_entry)
    if len(DECISION_LOG) > 50: DECISION_LOG.pop()
    if "⚠️" in message: asyncio.create_task(send_whatsapp_notification(f"ALERT: {message}"))

async def self_ping():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await asyncio.sleep(600) # 10 minutes
                await client.get(f"{RENDER_URL}/heartbeat")
            except: pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping())

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Antigravity Server</title></head>
        <body style="background:#0b0e14; color:#00f2fe; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh;">
            <h1>🚀 ANTIGRAVITY SERVER IS LIVE</h1>
            <p>Dashboard is active and waiting for telemetry.</p>
            <div style="border:1px solid #00f2fe; padding:20px; border-radius:10px;">
                Cihazlar bağlandığında veriler burada işlenecektir.
            </div>
        </body>
    </html>
    """

@app.get("/heartbeat")
async def heartbeat():
    return {"status": "alive", "timestamp": time.time()}

@app.post("/update")
async def update_device(data: dict):
    device_id = data.get("device_id", "unknown")
    DEVICES[device_id] = {**data, "last_seen": time.time()}
    if data.get("temp", 0) > 75: log_decision(f"⚠️ {device_id} aşırı ısındı!")
    return {"status": "ok"}

@app.get("/status")
async def get_status():
    current_time = time.time()
    active_devices = [info for info in DEVICES.values() if (current_time - info.get("last_seen", 0)) < 60]
    return {
        "devices": active_devices,
        "total_hashrate": sum(d.get("hashrate", 0) for d in active_devices),
        "decision_log": DECISION_LOG,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
