from fastapi import APIRouter, FastAPI

from app.routers import auth, user

app = FastAPI()
main_router = APIRouter(prefix="/api/v1")
main_router.include_router(user.router)
main_router.include_router(auth.router)
app.include_router(main_router)
