"""
Gemini AI Service for image inpainting
"""
import time
import base64
import io
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
            
            # Comprehensive automatic prompt - remove EVERYTHING except room structure
            auto_prompt = (
                "Remove EVERYTHING from this room to make it completely empty. "
                "Remove ALL of these items: "
                "- All furniture (sofa, bed, chair, table, desk, cabinet, almirah, wardrobe, dresser, shelf, bookcase) "
                "- All electrical appliances (TV, LCD, refrigerator, AC, fan, lights, lamps) "
                "- All decorative items (photo frames, paintings, mirrors, wall art, plants, vases, decorations) "
                "- All electronics (computer, speakers, cables, devices) "
                "- All textiles (curtains, drapes, rugs, carpets, cushions, bedding) "
                "- Any other objects, items, or belongings. "
                "Keep ONLY the bare room structure: plain walls, plain floor, plain ceiling, empty windows, and doors. "
                "Fill all removed areas with matching wall color, floor texture, or appropriate background. "
                "Make it look like a completely vacant, unfurnished room ready for new tenants."
            )
            print(f"Auto-detecting and removing ALL objects from room (furniture, appliances, decorations, etc.)...")
            
            # Call API directly - no retry, no delay
            response = self._call_api(auto_prompt, img)
            
            # Extract token usage
            token_info = self._extract_token_usage(response)
            
            # Extract the edited image from response
            result = self._extract_image_from_response(response, image_bytes, token_info)
            
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
