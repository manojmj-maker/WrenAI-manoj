import time
import logging
from fastapi import APIRouter

# Use the same logger name prefix so logs are formatted consistently
logger = logging.getLogger("vanilla-fastapi.samples")

# Standard APIRouter without any custom telemetry wrappers!
# OpenTelemetry's FastAPIInstrumentor handles everything automatically.
router = APIRouter(prefix="/api/samples", tags=["samples"])

@router.get("/users")
async def get_users():
    """
    Standard GET endpoint. 
    OTel will automatically generate a span, measure latency, and record metrics.
    """
    logger.info("Processing GET /api/samples/users")
    
    # Simulate some processing time (e.g., DB lookup)
    time.sleep(0.15)
    
    return {
        "message": "Fetched users automatically tracked by OTel!", 
        "data": ["Alice", "Bob"]
    }

@router.post("/items")
async def create_item():
    """
    Standard POST endpoint.
    OTel will automatically capture any errors or standard latency metrics here as well.
    """
    logger.info("Processing POST /api/samples/items")
    
    # Simulate processing delay
    time.sleep(0.25)
    
    return {
        "message": "Item created and automatically tracked!"
    }
