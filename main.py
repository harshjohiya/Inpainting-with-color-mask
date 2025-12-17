"""
FastAPI application for image inpainting using Gemini AI
"""
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import RATE_LIMIT
from gemini_service import GeminiService


# Initialize FastAPI app
app = FastAPI(title="Baseraa Inpainting API", version="1.0.0")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize Gemini service
gemini_service = GeminiService()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/inpaint")
@limiter.limit(RATE_LIMIT)
async def inpaint_endpoint(
    request: Request,
    image: UploadFile = File(...)
):
    """
    Automatic image segmentation endpoint - generates color-coded masks for each object
    
    Args:
        image: uploaded image file
    
    Returns:
        JSON with image_base64, color_mapping (RGB values for each object), 
        token_usage, and optionally error
    """
    # Read uploaded image bytes
    image_bytes = await image.read()
    
    # Process image with Gemini service - generates segmentation mask with unique colors
    result = gemini_service.inpaint_image(image_bytes)
    
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": gemini_service.is_configured()
    }
