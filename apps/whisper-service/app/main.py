"""
ASR Service for GreekSTT Research Platform
Handles Whisper and wav2vec2 models with transformers 4.36
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

# Environment variables for model stability
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# CUDA optimizations
os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"

# cuDNN library path fix
import sys
import os
from pathlib import Path

# ctranslate2 library path setup
try:
    import ctranslate2
    ct2_path = Path(ctranslate2.__file__).parent / "libs"
    if ct2_path.exists():
        # Add to LD_LIBRARY_PATH
        current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if str(ct2_path) not in current_ld_path:
            os.environ["LD_LIBRARY_PATH"] = f"{ct2_path}:{current_ld_path}" if current_ld_path else str(ct2_path)
except ImportError:
    pass

# CPU mode override
if os.environ.get("FORCE_CPU_MODE", "false").lower() == "true":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
else:

# Whisper configuration
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512,expandable_segments:True")
os.environ.setdefault("WHISPER_CACHE_DIR", "/app/models/whisper")
os.environ.setdefault("HF_HOME", "/app/models")
os.environ.setdefault("HF_HUB_CACHE", "/app/models/hf_hub_cache")
os.environ.setdefault("TORCH_HOME", "/app/models/torch_cache")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.transcription import router as transcription_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

logging.getLogger("torch").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("faster_whisper").setLevel(logging.INFO)
logging.getLogger("ctranslate2").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting GreekSTT Whisper Service")
    logger.info("Model: Whisper large-v3")
    logger.info("Library: faster-whisper + ctranslate2")
    
    # Pre-download and cache Whisper model
    try:
        logger.info("Pre-downloading and initializing Whisper large-v3 model...")
        from faster_whisper import WhisperModel
        import torch
        
        # GPU availability check
        if torch.cuda.is_available():
            device = "cuda"
            compute_type = "float16"
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            compute_type = "int8"
            logger.info("No GPU detected, using CPU")
        
        # Download and initialize model with optimal device
        model = WhisperModel(
            "large-v3", 
            device=device, 
            compute_type=compute_type,
            download_root="/app/models/whisper",
            num_workers=1
        )
        
        logger.info(f"✅ Whisper large-v3 model ready on {device.upper()}")
        logger.info(f"📊 Memory usage: {torch.cuda.memory_allocated() / 1024**3:.2f}GB" if device == "cuda" else "")
        
        # Keep model loaded for immediate use
        # Store in app state for reuse
        app.state.whisper_model = model
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Whisper model: {e}")
        logger.info("⚠️  Model will be loaded on first request")
        app.state.whisper_model = None
    
    yield
    
    logger.info("🔄 Shutting down GreekSTT Whisper Service")


# Create FastAPI app
app = FastAPI(
    title="GreekSTT Whisper Service",
    description="Academic Whisper service for Greek language research",
    version="1.0.0-whisper",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transcription_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "service": "GreekSTT Whisper Service",
        "version": "1.0.0-whisper",
        "description": "Academic Whisper service for Greek language research",
        "models": ["whisper-large-v3"],
        "library": "faster-whisper + ctranslate2",
        "endpoints": {
            "transcribe": "/api/v1/transcribe",
            "health": "/api/v1/health"
        }
    })


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )