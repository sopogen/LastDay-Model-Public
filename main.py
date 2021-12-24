import asyncio
import functools
import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import room_model
from app.dependencies.room_model import RoomModel
from app.dependencies.station_model import StationModel
from app.schema import *
from app.utils.log import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health_check():
    return {"ok": True}


@app.post("/room", response_model=ResponsePayload)
async def room_based(req: RoomRequestBody):
    response = dict()
    start_time: float = time.time()
    print("Request parameters", req.__dict__)
    func = functools.partial(
        RoomModel().get_room_based_spot,
        (req.source_x, req.source_y),
        (req.dest_x, req.dest_y),
        req.content_type,
        req.candidates,
        req.limit_time_hour,
        req.limit_time_min,
    )

    result = await asyncio.create_task(func())

    response = {
        "recommended": result,
        "time_taken": time.time() - start_time,
    }
    return response


@app.post("/station", response_model=ResponsePayload)
async def station_based(req: StationRequestBody):
    response = dict()
    start_time: float = time.time()

    func = functools.partial(
        StationModel().get_station_based_spot,
        (req.source_x, req.source_y),
        req.radius,
        req.content_type,
        req.candidates,
        req.limit_time_hour,
        req.limit_time_min,
    )

    result = await asyncio.create_task(func())

    response = {
        "recommended": result,
        "time_taken": time.time() - start_time,
    }
    return response
