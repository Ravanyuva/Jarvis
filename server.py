import asyncio
import json
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import jarvis_advanced
import database
import psutil

# --- AUTH CONFIG ---
SECRET_KEY = "jarvis_secret_key_change_this_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Extend Jarvis to emit events
class WebJarvis(jarvis_advanced.JarvisAssistant):
    def __init__(self):
        super().__init__()
        self.loop = None # Reference to asyncio loop

    def set_loop(self, loop):
        self.loop = loop

    def emit(self, event_type, data):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": event_type, "data": data}),
                self.loop
            )

    def speak(self, text):
        self.emit("speak", text)
        print(f"Jarvis: {text}") 
        super().speak(text)  # Now safe to call as it pushes to background queue
        
        # Log to DB
        # Note: We need the last user text and intent to log properly. 
        # For simplicity, we'll log here assuming it matches the last processed command.
        if hasattr(self.context, 'last_command') and hasattr(self.context, 'last_intent'):
             database.db.log_interaction(self.context.last_command, self.context.last_intent, text)



    def listen_once(self, timeout=8, phrase_time_limit=10):
        self.emit("status", "listening")
        text = super().listen_once(timeout, phrase_time_limit)
        if text:
            self.emit("transcript", text)
        self.emit("status", "idle")
        return text

# Global instance
jarvis = WebJarvis()

# --- AUTH MODELS & UTILS ---
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class SubscriptionUpdate(BaseModel):
    plan: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = database.db.get_user(username)
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ROUTES ---
@app.post("/api/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    hashed_pwd = get_password_hash(user.password)
    success = database.db.create_user(user.username, hashed_pwd, user.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already registered"
        )
    return {"message": "User created successfully"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = database.db.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Convert 'created_at' and 'timestamp' to str to avoid json serialization error
    if "created_at" in current_user:
        current_user["created_at"] = str(current_user["created_at"])
    if "_id" in current_user:
        current_user["_id"] = str(current_user["_id"])
    return current_user

@app.post("/api/subscription")
async def update_subscription_endpoint(sub: SubscriptionUpdate, current_user: dict = Depends(get_current_user)):
    success = database.db.update_subscription(current_user["username"], sub.plan)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update subscription")
    return {"message": f"Subscription updated to {sub.plan}"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Give the Jarvis instance access to the loop to broadcast events
        jarvis.set_loop(asyncio.get_event_loop())
        while True:
            data = await websocket.receive_text()
            # Handle commands from UI if needed
            msg = json.loads(data)
            if msg.get("action") == "start":
                # Start listener in background if not running
                if not getattr(jarvis, "running_thread", None):
                    jarvis.context.running = True
                    jarvis.running_thread = threading.Thread(target=jarvis.start_hotkey_listener)
                    jarvis.running_thread.daemon = True
                    jarvis.running_thread.start()
                    await manager.broadcast({"type": "status", "data": "started"})
            elif msg.get("action") == "stop":
                jarvis.context.running = False
                await manager.broadcast({"type": "status", "data": "stopped"})
            elif msg.get("action") == "command":
                # Manual text command input
                cmd = msg.get("text", "")
                if cmd:
                    # Support compound commands (e.g. "open notepad and type hello")
                    # Split by " and " (case-insensitive ideally, but simple split for now)
                    sub_commands = cmd.split(" and ")
                    
                    for sub_cmd in sub_commands:
                        sub_cmd = sub_cmd.strip()
                        if sub_cmd:
                             # Process intent
                            intent = jarvis.parse_intent(sub_cmd)
                            jarvis.handle_intent(intent)
                            
                            # Broadcast what we are doing
                            await manager.broadcast({"type": "transcript", "data": sub_cmd})
                            
                            # Small delay between chained commands to allow UI/App to catch up
                            if len(sub_commands) > 1:
                                await asyncio.sleep(1.5)
            elif msg.get("action") == "listen":
                 # Trigger listening via UI button (run in thread to not block WS)
                 def manual_listen():
                     text = jarvis.listen_once()
                     if text:
                         # Normalize text (remove punctuation)
                         text = text.replace(".", "").replace("?", "")
                         intent = jarvis.parse_intent(text)
                         
                         # Save context for DB logging
                         jarvis.context.last_command = text
                         jarvis.context.last_intent = intent.get("type", "unknown")
                         
                         jarvis.handle_intent(intent)
                 
                 threading.Thread(target=manual_listen).start()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"status": "Jarvis Backend Running"}

# Background Task for System Stats
async def broadcast_stats():
    while True:
        try:
            # Check for active connections in the manager
            if manager.active_connections:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                battery = psutil.sensors_battery()
                batt_pct = battery.percent if battery else 100
                
                stats_msg = {
                    "type": "stats",
                    "data": {
                        "cpu": cpu,
                        "ram": ram,
                        "battery": batt_pct
                    }
                }
                await manager.broadcast(stats_msg)
        except Exception as e:
            print(f"Stats Error: {e}")
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    import uvicorn
    print("Starting Jarvis Server...")
    
    # Start stats loop in background on startup logic is tricky with uvicorn.run
    # We will hook into the startup event via app state or just run it as a task if loop exists
    
    @app.on_event("startup")
    async def startup_event():
         asyncio.create_task(broadcast_stats())
         jarvis.start_background_listening()

    # Run uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
