from fastapi import FastAPI
from schemas.user import UserSignUpModel
from services.user_services import create_user
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from routers.auth import router as user_router
from routers.search import router as search_router
from routers.policies import router as policies_router
from services.cron_service import run_scheduled_sentiment_analysis

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting background cron jobs...")

    # For testing, change 'hours=12' to 'minutes=1' to see results quickly
    scheduler.add_job(
        run_scheduled_sentiment_analysis, 
        'interval', 
        hours=12,
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.start() 
    yield
    print("Shutting down background cron jobs...")
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL like "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(search_router)
app.include_router(policies_router)


@app.get('/')
def root():
    print('Civic Pulse')
    return {'message':'Hello FastAPI'}


