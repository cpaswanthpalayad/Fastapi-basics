from asyncio import create_task
import time
from fastapi import FastAPI, Request, WebSocket, status
from fastapi.responses import HTMLResponse, JSONResponse
from app.db import models, database
from app.exceptions import StoryException
from app.router import blog_get, blog_post, dependencies, file, product, user, article
from fastapi.middleware.cors import CORSMiddleware
from app.auth import authentication
from fastapi.staticfiles import StaticFiles
from app.client import html
from app.templates import templates

app = FastAPI()


app.include_router(dependencies.router)
app.include_router(templates.router)
app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(file.router)
app.include_router(article.router)
app.include_router(product.router)
app.include_router(blog_get.router)
app.include_router(blog_post.router)


@app.exception_handler(StoryException)
def story_exception_handler(request: Request, exc: StoryException):
    return JSONResponse(
        status_code=status.HTTP_418_IM_A_TEAPOT, content={"detail": exc.name}
    )


@app.get("/")
async def get():
    return HTMLResponse(html)


clients = []


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    while True:
        data = await websocket.receive_text()
        for client in clients:
            await client.send_text(data)


models.Base.metadata.create_all(database.engine)


@app.middleware("http")
async def add_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["duration"] = str(duration)
    return response


origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/files", StaticFiles(directory="files"), name="files")

app.mount("/templates/static", StaticFiles(directory="templates/static"), name="static")
