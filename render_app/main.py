from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
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
RENDER_URL = "https://your-app-name.onrender.com" # User should update this

# WhatsApp Configuration (CallMeBot - Free and easy to setup)
# User should get their API Key from https://www.callmebot.com/
WHATSAPP_PHONE = "+90..." 
WHATSAPP_API_KEY = "YOUR_KEY"

async def send_whatsapp_notification(message: str):
    """Sends notification via WhatsApp using CallMeBot."""
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={message}&apikey={WHATSAPP_API_KEY}"
            await client.get(url)
        except: pass

def log_decision(message: str):
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": message
    }
    DECISION_LOG.insert(0, log_entry)
    if len(DECISION_LOG) > 50:
        DECISION_LOG.pop()
    
    # Send critical alerts to WhatsApp
    if "⚠️" in message or "Critical" in message:
        asyncio.create_task(send_whatsapp_notification(f"ANTIGRAVITY ALERT: {message}"))

async def self_ping():
    """Self-ping mechanism to keep Render awake."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Ping every 12 minutes
                await asyncio.sleep(720) 
                response = await client.get(f"{RENDER_URL}/heartbeat")
                print(f"Self-ping status: {response.status_code}")
            except Exception as e:
                print(f"Self-ping failed: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping())

@app.get("/heartbeat")
async def heartbeat():
    return {"status": "alive", "timestamp": time.time()}

@app.post("/update")
async def update_device(data: dict):
    device_id = data.get("device_id", "unknown")
    DEVICES[device_id] = {
        **data,
        "last_seen": time.time()
    }
    
    # Simple Local AI Logic simulation on Backend
    if data.get("temp", 0) > 75:
        log_decision(f"⚠️ {device_id} overheated! Shifting load.")
        
    return {"status": "ok"}

@app.get("/status")
async def get_status():
    current_time = time.time()
    active_devices = []
    total_hashrate = 0
    
    for device_id, info in DEVICES.items():
        # Device is offline if not seen for 30 seconds
        is_online = (current_time - info.get("last_seen", 0)) < 30
        if is_online:
            active_devices.append(info)
            total_hashrate += info.get("hashrate", 0)
            
    return {
        "devices": active_devices,
        "total_hashrate": total_hashrate,
        "decision_log": DECISION_LOG,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/command")
async def send_command(command: dict):
    # Relay command to specific device or broadcast
    log_decision(f"📡 Command received: {command.get('type')}")
    return {"status": "broadcasted"}

# WhatsApp Webhook placeholder
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    # This would receive messages from a WhatsApp API like Twilio
    body = await request.form()
    msg = body.get("Body", "").upper()
    
    if "DURUM" in msg:
        # Return status via WhatsApp
        pass
    elif "GÜCÜ_ARTIR" in msg:
        log_decision("🚀 WhatsApp Command: GÜCÜ_ARTIR executed.")
        
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
