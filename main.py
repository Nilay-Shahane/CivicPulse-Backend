from fastapi import FastAPI
from schemas.user import UserSignUpModel
from services.user_services import create_user
from routers.auth import router as user_router
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL like "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)


@app.get('/')
def root():
    print('Civic Pulse')
    return {'message':'Hello FastAPI'}


