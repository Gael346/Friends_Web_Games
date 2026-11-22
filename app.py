from fastapi import FastAPI , WebSocket , WebSocketDisconnect , HTTPException , Request , Form
from werkzeug.security import check_password_hash, generate_password_hash
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3 

# Database 
conn = sqlite3.connect("messenger.db" , check_same_thread=False)
db = conn.cursor()

# FastApi config 
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def main(request: Request):
    return templates.TemplateResponse(request=request , name="index.html")

@app.get("/register_form")
async def register_form(request : Request):
    return templates.TemplateResponse(request=request , name="register.html")

@app.post("/register")
async def register(request : Request , username: str = Form() , password : str = Form()):
    return templates.TemplateResponse(request=request , name="index.html")