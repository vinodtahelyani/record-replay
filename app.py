from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from ws import WebSocketHandler
import uvicorn

app = FastAPI()

# Serve static files from the 'public' folder
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
async def root():
    return FileResponse("public/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    handler = WebSocketHandler(websocket)
    await handler.connect()
    while True:
        data = await handler.receive_message()
        if data is None:
            break
        await handler.handle_message(data)
    await handler.disconnect()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000,
                ssl_certfile="./lambdatestinternal.com.pem",
                ssl_keyfile="./lambdatestinternal.com-key.pem")