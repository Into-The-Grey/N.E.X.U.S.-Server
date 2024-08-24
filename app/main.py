from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
async def get():
    return HTMLResponse(
        """
    <html>
        <head>
            <title>WebSocket Test</title>
        </head>
        <body>
            <h1>WebSocket Test</h1>
            <button onclick="connect()">Connect</button>
            <script>
                let socket;
                function connect() {
                    socket = new WebSocket("ws://localhost:8000/ws");
                    socket.onmessage = function(event) {
                        alert("Message from server: " + event.data);
                    }
                    socket.onopen = function(event) {
                        socket.send("Hello Server!");
                    }
                }
            </script>
        </body>
    </html>
    """
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received: {data}")
