from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import google.generativeai as genai
from PIL import Image
import io

app = FastAPI()

# Configure Gemini API
# Paste your Gemini API key here
GEMINI_API_KEY = "AIzaSyDyb6cDl2cGxglHQOZ2dU6LJOfBRUf1wU4E"  # Replace this with your actual API key
if GEMINI_API_KEY and GEMINI_API_KEY != "PASTE_YOUR_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)

# If you later host frontend separately (React etc.), adjust origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    # simple way: read static HTML file
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/inpaint")
async def inpaint_endpoint(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    image: uploaded image (user file)
    prompt: text like "remove the fridge" or "remove the person on the left"
    """
    # 1) read uploaded image bytes
    image_bytes = await image.read()

    # 2) Check if API key is configured
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_API_KEY_HERE":
        # Return original image if no API key
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return {"image_base64": image_b64, "error": "API key not configured"}
    
    try:
        # 3) Load image with PIL
        img = Image.open(io.BytesIO(image_bytes))
        
        # 4) Use Gemini 2.0 Flash for image editing
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 5) Create prompt for image editing
        edit_prompt = f"""You are an expert image editor. {prompt}
        
Please analyze this image and provide detailed instructions on how to edit it to fulfill the request.
Describe what should be removed and how the background should be filled in naturally."""
        
        # 6) Generate response
        response = model.generate_content([edit_prompt, img])
        
        # 7) For now, return original image with AI analysis
        # Note: Gemini Flash doesn't directly edit images, it provides text analysis
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return {
            "image_base64": image_b64,
            "ai_response": response.text if response else "No response",
            "note": "Image analysis complete. Direct image editing requires additional tools."
        }
        
    except Exception as e:
        # Return original image with error
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return {"image_base64": image_b64, "error": str(e)}
