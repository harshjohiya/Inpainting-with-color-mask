# Baseraa - AI Image Inpainting Tool

A powerful web-based image inpainting application that uses Google's Gemini 2.5 Flash Image model to intelligently remove furniture and objects from images.

![Baseraa Logo](https://img.shields.io/badge/Baseraa-AI%20Inpainting-2db89f?style=for-the-badge)

## 🌟 Features

- **AI-Powered Object Removal**: Remove furniture, appliances, and objects from images using state-of-the-art AI
- **Simple Interface**: Just upload an image and type the item name to remove
- **Real-time Processing**: Fast, single-call API processing for quick results
- **Token Tracking**: Monitor input/output tokens for each operation
- **Rate Limiting**: Built-in protection against API abuse (5 requests/minute)
- **Responsive Design**: Clean, modern UI with Baseraa branding
- **Error Handling**: User-friendly error messages and fallback responses

## 📋 Prerequisites

- Python 3.13+ (or Python 3.8+)
- Google Gemini API Key ([Get one here](https://ai.google.dev/))
- Modern web browser

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd "inpainting main"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On Windows CMD:
venv\Scripts\activate.bat

# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY_1=your_gemini_api_key_here
```

**Important**: Never commit your `.env` file to git. It's already in `.gitignore`.

## ▶️ Running the Application

### Start the Server

```bash
# Make sure virtual environment is activated
python -m uvicorn main:app --reload
```

The server will start at: **http://127.0.0.1:8000**

### Access the Application

1. Open your browser
2. Navigate to `http://127.0.0.1:8000`
3. Upload an image
4. Type the item to remove (e.g., "sofa", "chair", "table")
5. Click "Inpaint"

## 📁 Project Structure

```
inpainting main/
├── main.py                 # FastAPI application (routes only)
├── gemini_service.py      # Gemini AI logic (API calls, image processing)
├── config.py              # Configuration settings
├── index.html             # Frontend UI
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API key)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### File Responsibilities

- **main.py**: Web server routes and HTTP handling
- **gemini_service.py**: All AI image processing logic
- **config.py**: Centralized configuration (API key, model name, rate limits)
- **index.html**: User interface with Baseraa branding

## 🛠️ Configuration

Edit `config.py` to customize:

```python
# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY_1')  # From .env file
MODEL_NAME = "gemini-2.5-flash-image"           # AI model to use

# Retry Configuration
MAX_RETRIES = 5      # Maximum retry attempts
BASE_DELAY = 5       # Base delay for retries (seconds)

# Rate Limiting
RATE_LIMIT = "5/minute"  # Requests per minute per IP
```

## 📡 API Endpoints

### `GET /`
Serves the main HTML interface.

### `POST /api/inpaint`
Performs image inpainting.

**Request:**
- `image`: Image file (multipart/form-data)
- `prompt`: Item name to remove (e.g., "sofa")

**Response:**
```json
{
  "image_base64": "base64_encoded_image",
  "token_usage": {
    "input_tokens": 264,
    "output_tokens": 1290,
    "total_tokens": 1554
  }
}
```

**Rate Limit:** 5 requests per minute per IP

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "gemini_configured": true
}
```

## 💡 Usage Examples

### Simple Object Removal
Just type the item name:
- `sofa`
- `chair`
- `table`
- `curtain`
- `fridge`

### Multiple Objects
Specify multiple items:
- `sofa and table`
- `chair and curtain`
- `bed and nightstand`

The system automatically constructs the full prompt:
```
"Remove [your_item] from this image and fill the space naturally to match the surrounding area."
```

## 🔧 Troubleshooting

### API Key Issues

**Error: "API key not configured"**
- Check your `.env` file exists
- Verify `GEMINI_API_KEY_1` is set correctly
- Restart the server after changing `.env`

### Import Errors

**Error: "cannot import name 'genai' from 'google'"**
```bash
pip install google-genai
```

### Rate Limit Errors

**Error: "429 Too Many Requests"**
- Wait 60 seconds before trying again
- Default limit is 5 requests/minute
- Adjust `RATE_LIMIT` in `config.py` if needed

### Model Not Returning Images

**Error: "Model did not return an edited image"**
- The `gemini-2.5-flash-image` model may not support all image editing tasks
- Try different prompts
- Check your API quota at [Google AI Studio](https://ai.google.dev/)

## 🔒 Security

- ✅ API keys stored in `.env` (not committed to git)
- ✅ Rate limiting prevents API abuse
- ✅ CORS configured (adjust for production)
- ✅ Input validation on all endpoints

**For Production:**
1. Update CORS origins in `main.py`
2. Use environment-specific `.env` files
3. Enable HTTPS
4. Add authentication if needed

## 🎨 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server with auto-reload
- **google-genai**: Google's Gemini AI SDK
- **Pillow**: Image processing library
- **SlowAPI**: Rate limiting middleware
- **python-dotenv**: Environment variable management

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript (Vanilla)**: No frameworks needed
- **Fetch API**: Async HTTP requests

### AI Model
- **Gemini 2.5 Flash Image**: Google's multimodal AI model

## 📊 Token Usage

Each API call consumes tokens:
- **Input tokens**: Based on prompt + image size
- **Output tokens**: Based on generated image

Monitor token usage in the UI after each inpainting operation.

## 🚧 Known Limitations

1. **Free Tier Quota**: Limited API calls per day with free API key
2. **Processing Time**: Depends on image size and complexity
3. **Model Capabilities**: May not perfectly remove all objects
4. **Image Size**: Large images consume more tokens

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and commercial use by Baseraa.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs in terminal
3. Verify API key and quota
4. Contact Baseraa support

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Initial release
- ✅ Gemini 2.5 Flash Image integration
- ✅ Simple prompt interface (item names only)
- ✅ Token usage tracking
- ✅ Rate limiting
- ✅ Modular code structure
- ✅ Baseraa branding

---

**Built with ❤️ by Baseraa**
