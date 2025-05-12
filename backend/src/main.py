import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, grsu, report


app = FastAPI()
image_path = os.path.join("images")

app.mount("/backend/images", StaticFiles(directory=image_path), name="images")
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Auth"], prefix="/auth")
app.include_router(grsu.router, tags=["Grsu"], prefix="/grsu")
app.include_router(report.router, tags=["Report"], prefix="/report")