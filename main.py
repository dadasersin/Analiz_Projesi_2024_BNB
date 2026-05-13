from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import time
import os
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

# Ensure dashboard directory exists for static files if needed
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")

async def send_whatsapp_notification(message: str):
    """Sends notification via WhatsApp using CallMeBot."""
    if WHATSAPP_API_KEY == "YOUR_KEY": return
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
                await asyncio.sleep(600) # 10 minutes
                response = await client.get(f"{RENDER_URL}/heartbeat")
                print(f"Self-ping status: {response.status_code}")
            except Exception as e:
                print(f"Self-ping failed: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping())
    log_decision("🚀 Command Center Online and Ready.")

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(DASHBOARD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return """
    <html>
        <body style="background:#0b0e14; color:#00f2fe; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh;">
            <h1>🚀 ANTIGRAVITY SERVER IS LIVE</h1>
            <p>Dashboard file missing. Please check /render_app/dashboard/index.html</p>
        </body>
    </html>
    """

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
    
    # Logic: If temperature is critical
    if data.get("temp", 0) > 75:
        log_decision(f"⚠️ {device_id} HIGH TEMP: {data['temp']}°C! Emergency throttling.")
        
    return {"status": "ok"}

@app.get("/status")
async def get_status():
    current_time = time.time()
    active_devices = []
    total_hashrate = 0
    
    # Clean up old devices (older than 2 minutes)
    to_delete = []
    for device_id, info in DEVICES.items():
        is_online = (current_time - info.get("last_seen", 0)) < 60
        if is_online:
            active_devices.append(info)
            total_hashrate += info.get("hashrate", 0)
        elif (current_time - info.get("last_seen", 0)) > 300:
            to_delete.append(device_id)
            
    for d in to_delete: del DEVICES[d]
            
    return {
        "devices": active_devices,
        "total_hashrate": total_hashrate,
        "decision_log": DECISION_LOG,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/command")
async def send_command(command: dict):
    log_decision(f"📡 Command received: {command.get('type')}")
    return {"status": "broadcasted"}

@app.get("/unmineable")
async def get_unmineable_stats():
    wallet = "0xb71ddf8f661490314455dff6625b41eadf950701"
    coin = "BNB"
    api_url = f"https://api.unmineable.com/v4/address/{wallet}?coin={coin}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Use port from environment variable for Render
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
