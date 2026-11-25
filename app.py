from werkzeug.security import check_password_hash, generate_password_hash
from fastapi import FastAPI , WebSocket , WebSocketDisconnect , HTTPException , Request , Form 
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import websockets
import sqlite3
import random 
from enum import Enum

class State(Enum):
    START = 1,
    VOTE = 2,
    RANKING = 3,
    CHANGE = 4,
    GAME1 = 5,
    GAME2 = 6


class roomManager():
    def __init__(self, room_name:str , players_num:int , minigames_num:int ):
        self.room_name = room_name
        self.players_num = players_num
        self.minigames = minigames_num
        self.playing = 0
        self.state = State.START

    def change_state(self , new_state : State):
        if self.state == State.CHANGE:
            self.state = new_state



# Database 
conn = sqlite3.connect("database.db" , check_same_thread=False)
db = conn.cursor()

# FastApi configs
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def main(request: Request):
    id = request.cookies.get("id")
    return templates.TemplateResponse(request=request , name="index.html", context=locals())

# Rooms structure 
rooms = { str : { 
    "dates" : roomManager,
    "conected" : {
        "username" : {
            "websocket" : WebSocket ,
            "info" : {}
        }
    }
}}

@app.get("/join_room_form")
def join_room_form(request : Request):
    return templates.TemplateResponse(request=request , name="join_room.html")

# Chek code and render the template for join to the room
@app.post("/join_room")
def join_room(request : Request , code : str = Form(default="")):
    if code in rooms:

        # Get username 
        db.execute("SELECT user_name FROM users WHERE id = ?" , (request.cookies.get("id"),))
        users_db = db.fetchall()
        if len(users_db) != 1:
          return RedirectResponse(url="/register_form" , status_code=303)
        username = users_db[0][0]

        return templates.TemplateResponse(request=request ,  name="room.html" , context={
            "code" : code,
            "room_name" : rooms[code]["dates"].room_name,
            "username" : username ,
            "users" : list(rooms[code]["conected"].keys())
        })
    return RedirectResponse(url="/join_room_form" , status_code=303)


@app.get("/create_room_form")
def create_room_form(request : Request):
    return templates.TemplateResponse(request=request , name="create_room.html")

# Create a room with the data recived
@app.post("/create_room")
def create_room(request: Request, room_name: str = Form(default="MyRoom") , players_num: int = Form(default=4) , minigames_num : int = Form(default=3)):
    # Generate code and chek is new 
    code = str(random.randint(1000 , 9999))
    if not code in rooms:
        rooms[code] = {}
        roomMan = roomManager(room_name , players_num , minigames_num)
        rooms[code]["dates"] = roomMan
        rooms[code]["conected"] = {}

    # Get username 
    db.execute("SELECT user_name FROM users WHERE id = ?" , (request.cookies.get("id"),))
    users_db = db.fetchall()
    if len(users_db) != 1:
        return RedirectResponse(url="/register_form" , status_code=303)
    username = users_db[0][0]

    return templates.TemplateResponse(request=request ,  name="room.html" , context={
        "code" : code,
        "room_name" : room_name,
        "username" : username ,
        "users" : [] 
    })

@app.websocket("/ws/{code}/{username}")
async def conections(websocket : WebSocket , code : str , username : str):

    # Check room is valid
    if not code in rooms or rooms[code]["dates"].playing >= rooms[code]["dates"].players_num:
       await websocket.close()
       return

    # Insert user into the room
    await websocket.accept()
    rooms[code]["conected"][username] = {
        "websocket" : websocket ,
        "info" : 
        {
            "points" : 0
        }
    }
    rooms[code]["dates"].playing += 1

    # Insert user in : users conected card 
    for user , data in rooms[code]["conected"].items():
                await data["websocket"].send_json({
                    "type" : "join",
                    "value" : username
                })

    try :
        # Recive and send data
        while True: 
            recive_data = await websocket.receive_json()

            for user , data in rooms[code]["conected"].items():
                await data["websocket"].send_json({
                    "type" : recive_data["type"],
                    "value" : recive_data["value"]
                })

    except WebSocketDisconnect:
        # If user disconects , eliminate it 
        del rooms[code]["conected"][username]


@app.get("/login_form")
async def login_form(request : Request):
    return templates.TemplateResponse(request=request , name="login.html")

@app.post("/login")
async def login(request : Request , username: str = Form(default="") , password : str = Form(default="")):
    # Check Inputs 
    if not username or not password:
        return RedirectResponse(url="/login_form", status_code=303)

    # Check username and password are corrects
    db.execute("SELECT * FROM users WHERE user_name = ?", (username,))
    users_db = db.fetchall()
    if len(users_db) != 1:
        return RedirectResponse(url="/login_form", status_code=303)

    # Check password
    id , username_db , password_db = users_db[0]
    if check_password_hash(password_db , password ) == False:
        return RedirectResponse(url="/login_form", status_code=303)
    
    # Set the cookie
    redirect = RedirectResponse(url='/' , status_code=303) 
    redirect.set_cookie(key="id", value=id)
    return redirect


# The regist form 
@app.get("/register_form")
async def register_form(request : Request):
    return templates.TemplateResponse(request=request , name="register.html")

# For insert dates 
@app.post("/register")
async def register(request : Request , username: str = Form(default="") , password : str = Form(default="") , confirm_password : str = Form(default="")):

    # Check Inputs 
    if not username or not password:
        return RedirectResponse(url="/register_form", status_code=303)
    elif password != confirm_password:    
        return RedirectResponse(url="/register_form", status_code=303)

    # Check username don't exist 
    db.execute("SELECT * FROM users WHERE user_name = ?", (username,))
    users_db = db.fetchall()
    if len(users_db) != 0:
        return RedirectResponse(url="/register_form", status_code=303)

    #Insert username ans password hashed
    db.execute("INSERT INTO users(user_name , password) VALUES(?,?)" , (username , generate_password_hash(password)))
    conn.commit()

    # Add cookie and redirect
    db.execute("SELECT id FROM users WHERE user_name = ?" , (username,))
    id = db.fetchall()[0][0]
    redirect = RedirectResponse(url='/' , status_code=303) 
    redirect.set_cookie(key="id", value=id)
    return redirect

