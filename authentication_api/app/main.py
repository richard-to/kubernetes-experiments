from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from . import models
from .db import engine
from .routers import accounts


models.Base.metadata.create_all(bind=engine)


app = FastAPI()


origins = []


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["accounts"],
)
