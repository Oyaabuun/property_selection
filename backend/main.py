from fastapi import FastAPI
from pydantic import BaseModel
from decision_engine import evaluate_property

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Property Decision AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DecisionInput(BaseModel):
    address: str | None = None
    lat: float | None = None
    lng: float | None = None

    asking_price: int
    property_type: str = "2bhk"
    radius_m: int = 2000


@app.post("/decision")
async def decision(inp: DecisionInput):
    return await evaluate_property(inp.dict())
