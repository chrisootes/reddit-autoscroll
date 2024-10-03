import logging
from contextlib import asynccontextmanager

import fastapi
from fastapi import staticfiles
from fastapi.middleware import cors
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from . import config
from . import api

logging.basicConfig(filename='backend.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("FRONTEND_DIR: "+config.FRONTEND_DIR)

@asynccontextmanager
async def lifespan(app_l: fastapi.FastAPI):
    # Do something before server starts
    FastAPICache.init(InMemoryBackend())

    # Run server loop
    yield

    # Do something after server stops
    await api.reddit.close()

app = fastapi.FastAPI(lifespan=lifespan)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@app.get("/clear")
async def clear():
    return await FastAPICache.clear()

app.include_router(api.router)

# Static frontend files
app.mount("/", staticfiles.StaticFiles(directory=config.FRONTEND_DIR, html = True), name="frontend")
