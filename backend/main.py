import logging
from contextlib import asynccontextmanager

import fastapi
from fastapi import staticfiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import asyncpraw

from . import config
from . import api

logging.basicConfig(filename='backend.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("FRONTEND_DIR: "+config.FRONTEND_DIR)

@asynccontextmanager
async def lifespan(app_l: fastapi.FastAPI):
    # Do something before server starts
    FastAPICache.init(InMemoryBackend())
    api.reddit = asyncpraw.Reddit(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        username=config.USERNAME,
        password=config.PASSWORD,
        user_agent=config.USERNAME,
        redirect_uri=config.HOSTNAME)

    # Run server loop
    yield

    # Do something after server stops
    await api.reddit.close()

app = fastapi.FastAPI(lifespan=lifespan)

@app.get("/clear")
async def clear():
    return await FastAPICache.clear()

app.include_router(api.router)

# Static frontend files
app.mount("/", staticfiles.StaticFiles(directory=config.FRONTEND_DIR, html = True), name="frontend")
