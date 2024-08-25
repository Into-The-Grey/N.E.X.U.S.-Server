import logging
import os
import sys
import psycopg2
import asyncio
import random
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/nexus.env", verbose=True, override=True
)

app = FastAPI()

# Configure logging
log_file = "/home/ncacord/N.E.X.U.S.-Server/app/logs/websocket_server.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("websocket_logger")

# Database connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Global variable to store server state
server_running = True


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        logger.info("N.E.X.U.S.-Core to N.E.X.U.S.-Client ESTABLISHED")
        return conn
    except psycopg2.Error as pe:
        logger.error(f"N.E.X.U.S.-Core connection was NOT ESTABLISHED: {str(pe)}")
        return None


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
            <button onclick="sendStop()">Stop Backend</button>
            <button onclick="sendStart()">Start Backend</button>
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
                
                function sendStop() {
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send("STOP_SERVER");
                    }
                }
                
                function sendStart() {
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send("START_SERVER");
                    }
                }
            </script>
        </body>
    </html>
    """
    )


def should_log_message(message: str) -> bool:
    """
    Determine if a message should be logged based on its content, frequency, and randomness.

    Args:
        message (str): The message content.

    Returns:
        bool: True if the message should be logged, False otherwise.
    """
    # Simple conditions to log errors or important messages
    if "error" in message.lower() or "important" in message.lower():
        return True

    # Randomly log 1 out of every 5 messages to prevent excessive logging
    if random.randint(1, 5) == 1:
        return True

    # Log messages that are particularly short or long as they may be unusual
    if len(message) < 10 or len(message) > 100:
        return True

    # If none of the conditions are met, don't log the message
    return False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global server_running
    await websocket.accept()
    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
            if data == "STOP_SERVER":
                server_running = False
                logger.info("Server stopped by client request.")
                await websocket.send_text("Server stopped.")
            elif data == "START_SERVER":
                server_running = True
                logger.info("Server started by client request.")
            else:
                if server_running:
                    if should_log_message(data):
                        logger.info(f"Message received: {data}")
                    await websocket.send_text(f"Message received: {data}")
                else:
                    await websocket.send_text("Server is currently stopped.")
    except asyncio.TimeoutError:
        logger.info("WebSocket receive timeout")
    except WebSocketDisconnect:
        logger.info("Client disconnected")


if __name__ == "__main__":
    # Test database connection on startup
    db_conn = get_db_connection()
    if db_conn:
        db_conn.close()
