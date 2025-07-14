"""
ASR Service for GreekSTT Research Platform
Handles Whisper and wav2vec2 models with transformers 4.36
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

# Set environment variables for model stability before any imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# CUDA 12 / cuDNN 8 optimizations
os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"

# Fix cuDNN library path for faster-whisper
import sys
import os
from pathlib import Path

# Find ctranslate2 bundled cuDNN path
try:
    import ctranslate2
    ct2_path = Path(ctranslate2.__file__).parent / "libs"
    if ct2_path.exists():
        # Add ctranslate2 libs to LD_LIBRARY_PATH
        current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if str(ct2_path) not in current_ld_path:
            os.environ["LD_LIBRARY_PATH"] = f"{ct2_path}:{current_ld_path}" if current_ld_path else str(ct2_path)
            print(f"📚 Added ctranslate2 libs to LD_LIBRARY_PATH: {ct2_path}")
except ImportError:
    pass

# Force CPU mode if environment variable is set (for debugging)
if os.environ.get("FORCE_CPU_MODE", "false").lower() == "true":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    print("🔄 FORCE_CPU_MODE enabled - running on CPU only")
else:
    print("🚀 GPU mode enabled with CUDA 12 / cuDNN 8 support")

# Configuration settings for ASR models
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512,expandable_segments:True")
os.environ.setdefault("TRANSFORMERS_CACHE", "/app/models/transformers_cache")
os.environ.setdefault("HF_HOME", "/app/models/hf_home")
os.environ.setdefault("HF_HUB_CACHE", "/app/models/hf_hub_cache")
os.environ.setdefault("TORCH_HOME", "/app/models/torch_cache")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.transcription import router as transcription_router

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporarily DEBUG to see segment issues
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 Starting GreekSTT ASR Service")
    logger.info("   Models: Whisper large-v3, wav2vec2-greek")
    logger.info("   Transformers: 4.36.0 (ASR-optimized)")
    
    yield
    
    logger.info("🔄 Shutting down GreekSTT ASR Service")


# Create FastAPI app
app = FastAPI(
    title="GreekSTT ASR Service",
    description="Academic ASR service for Whisper and wav2vec2 models",
    version="1.0.0-asr",
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
        "service": "GreekSTT ASR Service",
        "version": "1.0.0-asr",
        "description": "Academic ASR models for Greek language research",
        "models": ["whisper-large-v3", "wav2vec2-greek"],
        "transformers_version": "4.36.0",
        "endpoints": {
            "whisper_only": "/api/v1/transcribe/whisper",
            "wav2vec2_only": "/api/v1/transcribe/wav2vec2", 
            "comparison": "/api/v1/transcribe/compare",
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