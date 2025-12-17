"""
Gemini AI Service for image inpainting
"""
import time
import base64
import io
import numpy as np
from collections import Counter
from google import genai
from google.genai import types
from PIL import Image
from config import GEMINI_API_KEY, MODEL_NAME, MAX_RETRIES, BASE_DELAY


class GeminiService:
    """Service class for interacting with Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client"""
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            print("✓ Gemini API configured successfully")
        else:
            self.client = None
            print("WARNING: GEMINI_API_KEY not found in environment variables!")
            print("Please set GEMINI_API_KEY in your .env file or environment")
    
    def is_configured(self):
        """Check if API is properly configured"""
        return self.client is not None
    
    def inpaint_image(self, image_bytes: bytes) -> dict:
        """
        Perform automatic image inpainting - removes all furniture and objects
        
        Args:
            image_bytes: Raw image bytes
        
        Returns:
            dict with keys: image_base64, token_usage, and optionally error
        """
        if not self.client:
            return {
                "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
                "error": "API key not configured"
            }
        
        try:
            # Load image with PIL
            img = Image.open(io.BytesIO(image_bytes))
            
            # Comprehensive automatic prompt - create a flat segmentation mask for object selection
            auto_prompt = (
                "TASK:\n"
"Generate an INSTANCE SEGMENTATION MASK IMAGE from the uploaded room photo.\n\n"

"This output must be a COMPLETELY FLAT MASK IMAGE used for visual object selection and segmentation.\n\n"

"This is NOT a realistic photo.\n"
"This is a computer-vision style mask like Photoshop or COCO instance masks.\n\n"

"STEP 1 — OBJECT DETECTION:\n"
"Detect ALL visible objects in the image.\n\n"

"Target object categories MUST include but are not limited to:\n"
"- Furniture: bed, sofa, chair, table, wardrobe, cabinet, desk, shelf, almirah, stool, ottoman\n"
"- Decorative items: painting, photo frame, mirror, plant, vase, rug, carpet, wall art, sculpture\n"
"- Electrical appliances: TV, monitor, fan, AC, lamp, light, refrigerator, speaker, router\n\n"

"DO NOT INCLUDE these in the segmentation:\n"
"- Walls\n"
"- Floor\n"
"- Ceiling\n"
"- Doors\n"
"- Windows\n"
"- Curtains\n\n"

"Each INDIVIDUAL object instance must be detected separately.\n"
"Example: Chair #1 and Chair #2 are two different instances with different colors.\n\n"

"STEP 2 — INSTANCE-WISE COLOR MASKING:\n"
"Create a MASK IMAGE where EACH INDIVIDUAL OBJECT has ONE UNIQUE SOLID COLOR.\n\n"

"No two objects are allowed to share the same color.\n"
"Even objects of the same type must use different colors.\n\n"

"Use BRIGHT, DISTINCT colors that are easily distinguishable:\n"
"- Use vivid RGB colors like: red, green, blue, yellow, magenta, cyan, orange, purple, pink, lime\n"
"- Each object gets a completely different color\n"
"- Example: Sofa #1 → solid red (#FF0000), Sofa #2 → solid blue (#0000FF)\n"
"- Example: Chair #1 → solid green (#00FF00), Chair #2 → solid yellow (#FFFF00)\n"
"- Lamp → solid magenta (#FF00FF), TV → solid cyan (#00FFFF)\n\n"

"Each object must be filled COMPLETELY with one flat color using a paint-bucket style fill.\n\n"

"STEP 3 — BACKGROUND MASKING:\n"
"All non-target areas MUST be PURE BLACK (#000000).\n\n"

"Background includes: walls, floor, ceiling, windows, doors, curtains, empty space.\n\n"

"ABSOLUTE RULES:\n"
"1. NO realistic appearance — this is a segmentation mask, not a photo."
"2. NO textures."
"3. NO gradients."
"4. NO shading."
"5. NO shadows."
"6. NO lighting effects."
"7. NO reflections."
"8. NO transparency."
"9. NO outlines or borders."
"10. ONLY flat, solid, uniform colors."
"11. Sharp, precise boundaries following object edges exactly."
"12. Use vivid, high-contrast colors that are easily distinguishable."

"FINAL OUTPUT REQUIREMENT:"
"Produce a single flat instance-segmentation mask image."
"Colorful object regions must appear on a pure black background."
"The result must allow users to easily visually identify and segment objects in the frontend UI."

            )
            print(f"Creating instance segmentation mask with unique colors for each object...")
            
            # Call API directly - no retry, no delay
            response = self._call_api(auto_prompt, img)
            
            # Extract token usage
            token_info = self._extract_token_usage(response)
            
            # Extract the edited image from response
            result = self._extract_image_from_response(response, image_bytes, token_info)
            
            # Extract color mapping from the mask if image was successfully generated
            if result.get("image_base64") and not result.get("error"):
                color_mapping = self._extract_colors_from_mask(result["image_base64"])
                result["color_mapping"] = color_mapping
            
            return result
            
        except Exception as e:
            return self._handle_error(e, image_bytes)
    
    def _call_api(self, prompt: str, img: Image.Image):
        """Call Gemini API once - no retries"""
        print("Calling Gemini API...")
        
        # ACTUAL API CALL - single call, no retry
        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, img],
        )
        
        print("✓ API call successful!")
        return response
    
    def _extract_token_usage(self, response) -> dict:
        """Extract token usage information from API response"""
        token_info = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        # Debug: print response structure
        print(f"Response received. Has parts: {hasattr(response, 'parts')}")
        if hasattr(response, 'parts'):
            print(f"Number of parts: {len(response.parts)}")
        
        if hasattr(response, 'usage_metadata'):
            token_info["input_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0)
            token_info["output_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0)
            token_info["total_tokens"] = getattr(response.usage_metadata, 'total_token_count', 0)
            print(f"Token usage: {token_info}")
        
        return token_info
    
    def _extract_image_from_response(self, response, original_bytes: bytes, token_info: dict) -> dict:
        """Extract the edited image from Gemini API response"""
        print(f"DEBUG: Response has {len(response.parts)} parts")
        
        for i, part in enumerate(response.parts):
            print(f"DEBUG: Part {i} - has text: {part.text is not None}, has inline_data: {part.inline_data is not None}")
            
            # Check if this part contains inline image data FIRST
            if part.inline_data is not None:
                print("✓ Found inline image data!")
                # Get raw bytes directly from inline_data
                result_bytes = part.inline_data.data
                image_b64 = base64.b64encode(result_bytes).decode("utf-8")
                
                return {
                    "image_base64": image_b64,
                    "token_usage": token_info
                }
            
            # Check if this part contains text
            elif part.text is not None and len(part.text) > 0:
                print(f"⚠️ Got text response (first 200 chars): {part.text[:200]}")
        
        # Fallback: return original with error message
        print("❌ No image data found in response - model likely doesn't support image editing")
        image_b64 = base64.b64encode(original_bytes).decode("utf-8")
        return {
            "image_base64": image_b64,
            "error": "Model did not return an edited image. The 'gemini-2.5-flash-image' model may not support image editing/inpainting.",
            "token_usage": token_info
        }
    
    def _extract_colors_from_mask(self, image_base64: str) -> list:
        """Extract unique RGB colors from the generated mask image"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array for faster processing
            img_array = np.array(img)
            
            # Reshape to list of RGB pixels
            pixels = img_array.reshape(-1, 3)
            
            # Count unique colors
            unique_colors = {}
            for pixel in pixels:
                color_tuple = tuple(pixel)
                if color_tuple in unique_colors:
                    unique_colors[color_tuple] += 1
                else:
                    unique_colors[color_tuple] = 1
            
            # Sort by pixel count (most common first) and filter out black (background)
            sorted_colors = sorted(unique_colors.items(), key=lambda x: x[1], reverse=True)
            
            # Extract colors (excluding black background)
            color_list = []
            object_number = 1
            
            for color, pixel_count in sorted_colors:
                r, g, b = color
                
                # Skip black (background) and very dark colors
                if r < 10 and g < 10 and b < 10:
                    continue
                
                # Skip if too few pixels (noise)
                if pixel_count < 100:  # threshold for minimum object size
                    continue
                
                color_list.append({
                    "object_id": object_number,
                    "rgb": {"r": int(r), "g": int(g), "b": int(b)},
                    "hex": f"#{r:02X}{g:02X}{b:02X}",
                    "pixel_count": int(pixel_count)
                })
                object_number += 1
                
                # Limit to reasonable number of objects
                if object_number > 50:
                    break
            
            print(f"✓ Extracted {len(color_list)} unique object colors from mask")
            return color_list
            
        except Exception as e:
            print(f"⚠️ Error extracting colors from mask: {e}")
            return []
    
    def _handle_error(self, error: Exception, original_bytes: bytes) -> dict:
        """Handle errors and return appropriate response"""
        error_msg = str(error)
        
        # Check for specific error types
        if "429" in error_msg or "quota" in error_msg.lower():
            error_msg = (
                "⚠️ API Quota Exceeded: You've reached your free tier limit. "
                "Please check your billing at https://ai.google.dev/"
            )
        elif "401" in error_msg or "invalid" in error_msg.lower():
            error_msg = "🔑 Invalid API Key: Please check your Gemini API key configuration"
        elif "403" in error_msg or "permission" in error_msg.lower():
            error_msg = "🚫 Permission Denied: Your API key doesn't have access to this model"
        
        print(f"Error occurred: {error_msg}")
        
        image_b64 = base64.b64encode(original_bytes).decode("utf-8")
        return {
            "image_base64": image_b64,
            "error": error_msg,
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        }
