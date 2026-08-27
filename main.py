import time
from typing import Dict, Any, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Schemas & Enums
class CategoryEnum(str, Enum):
    ORDERS = "orders"
    RESTAURANT = "restaurant"
    CUSTOMER = "customer"
    GENERAL = "general"


class UserMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, example="Can you check my sales for today?")
    context_data: Optional[Dict[str, Any]] = Field(default=None, example={"merchant_id": "m_123"})


class BotResponse(BaseModel):
    reply: str
    category: CategoryEnum
    confidence: float
    processed_at: float


# Application Initialization
app = FastAPI(
    title="Merchant Insight AI Engine",
    version="2.0.0",
    description="Advanced contextual assistant for merchant performance, order analytics, and customer insights."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Modular Logic / Intent Engine
class IntentEngine:
    INTENT_MAP = {
        CategoryEnum.ORDERS: ["order", "sale", "revenue", "transaction", "checkout", "refund"],
        CategoryEnum.RESTAURANT: ["restaurant", "food", "kitchen", "menu", "dish", "table"],
        CategoryEnum.CUSTOMER: ["customer", "client", "buyer", "retention", "user", "feedback"],
    }

    @classmethod
    def analyze(cls, text: str) -> tuple[CategoryEnum, float, str]:
        text_lower = text.lower()
        
        for category, keywords in cls.INTENT_MAP.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                confidence = round(min(0.6 + (len(matches) * 0.2), 0.99), 2)
                reply_msg = f"I noticed you are asking about {category.value} ({', '.join(matches)}). Here is your automated analysis."
                return category, confidence, reply_msg

        return (
            CategoryEnum.GENERAL,
            0.50,
            "I can assist with merchant analytics, revenue trends, customer retention, and operational data."
        )


# API Routes
@app.get("/", tags=["Health"])
def home():
    return {"status": "active", "service": "Merchant Insight Engine v2.0"}


@app.get("/v1/healthz", tags=["Health"])
def health():
    return {"status": "ok", "uptime": "operational"}


@app.get("/v1/metadata", tags=["Metadata"])
def metadata():
    return {
        "name": "Merchant Insight Engine",
        "version": "2.0.0",
        "capabilities": ["orders", "restaurant", "customer", "general"],
        "author": "Seneha Ghosh"
    }


@app.post("/v1/reply", response_model=BotResponse, tags=["Core AI"])
def reply(payload: UserMessageRequest):
    try:
        category, confidence, reply_text = IntentEngine.analyze(payload.message)
        return BotResponse(
            reply=reply_text,
            category=category,
            confidence=confidence,
            processed_at=time.time()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing intent: {str(exc)}"
        )


@app.post("/v1/context", tags=["Context Engine"])
def receive_context(payload: Dict[str, Any]):
    if not payload:
        raise HTTPException(status_code=400, detail="Context payload cannot be empty.")
    return {"status": "success", "received_keys": list(payload.keys())}


@app.post("/v1/tick", tags=["System Lifecycle"])
def process_tick(payload: Dict[str, Any]):
    return {"status": "tick acknowledged", "timestamp": time.time(), "payload_received": payload}