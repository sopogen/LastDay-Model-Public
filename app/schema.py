from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RoomRequestBody(BaseModel):
    source_x: float = Field(..., example=126.938389155713)
    source_y: float = Field(..., example=37.5655576723744)
    dest_x: float = Field(..., example=126.93698075993808)
    dest_y: float = Field(..., example=37.555198169366435)
    content_type: int = 12
    candidates: int = 10
    limit_time_hour: int = 15
    limit_time_min: int = 30


class StationRequestBody(BaseModel):
    source_x: float = Field(..., example=126.93698075993808)
    source_y: float = Field(..., example=37.555198169366435)
    radius: Optional[int] = 10000
    content_type: int = 12
    candidates: int = 10
    limit_time_hour: int = 15
    limit_time_min: int = 30


class ResponsePayload(BaseModel):
    recommended: List
    time_taken: float


class Error:
    error_message: str

    def to_json(self) -> Dict:
        return {"error_message": self.error_message}


class ErrorBody(BaseModel):
    error_message: str

    @classmethod
    def from_error(cls, error: Error):
        return cls(error_message=error.error_message)
