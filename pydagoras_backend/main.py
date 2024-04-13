from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

import gbp_usd_eur_dag
import asyncio

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.counter = 5
app.D = gbp_usd_eur_dag.MyDAG('./mr/data/gbp_usd_eur.png')
app.D.set_input('eur-gbp',1)

app.add_middleware(
CORSMiddleware,
allow_origins=["*"], # Allows all origins
allow_credentials=True,
allow_methods=["*"], # Allows all methods
allow_headers=["*"], # Allows all headers
)

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    # open dag socket
    # pump_dag

    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    msg = app.D.G.to_string()
    await manager.broadcast(msg)
    #await manager.broadcast(f"Client #{client_id} joined the chat")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        #await manager.broadcast(f"Client #{client_id} left the chat")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.patch("/items/{item_id}")
async def update_item(item_id:str, value:float):
    app.counter += 1
    #app.D.set_input('eur-gbp',2)
    app.D.set_input(item_id, value)

    #await asyncio.sleep(2)

    msg = app.D.G.to_string()
    await manager.broadcast(msg)

    #await manager.broadcast(f'MH eg_dag ... {app.counter=}')
    return {"item_name ?? out put ??" }



