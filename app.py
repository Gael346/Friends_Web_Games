from fastapi import FastAPI , WebSocket , WebSocketDisconnect , HTTPException , Request
from werkzeug.security import check_password_hash, generate_password_hash
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def main(request: Request):
    return templates.TemplateResponse(request=request , name="index.html")