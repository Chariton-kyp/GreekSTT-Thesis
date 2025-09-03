"""
wav2vec2 ASR Service for GreekSTT Comparison Platform
Handles wav2vec2 models with transformers 4.36
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"

from pathlib import Path
if os.environ.get("FORCE_CPU_MODE", "false").lower() == "true":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
else:
    pass  # CUDA environment already configured
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512,expandable_segments:True")
os.environ.setdefault("TRANSFORMERS_CACHE", "/app/models/transformers_cache")
os.environ.setdefault("WAV2VEC2_CACHE_DIR", "/app/models/wav2vec2")
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
logging.getLogger("datasets").setLevel(logging.WARNING)
logging.getLogger("accelerate").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting GreekSTT wav2vec2 Service")
    logger.info("Model: wav2vec2-large-xlsr-53-greek")
    logger.info("Library: transformers + PyTorch")
    
    try:
        logger.info("Pre-downloading and initializing wav2vec2 Greek model...")
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        import torch
        
        if torch.cuda.is_available():
            device = "cuda"
            
            # Set GPU memory fraction (40% for wav2vec2 service)
            from app.core.config import config
            gpu_fraction = config.GPU_MEMORY_FRACTION
            total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            allocated_memory = total_memory * gpu_fraction
            
            # Set memory limit
            torch.cuda.set_per_process_memory_fraction(gpu_fraction, device=0)
            
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"Total GPU memory: {total_memory:.1f}GB")
            logger.info(f"Allocated to wav2vec2: {allocated_memory:.1f}GB ({gpu_fraction*100:.0f}%)")
        else:
            device = "cpu"
            logger.info("No GPU detected, using CPU")
        
        processor = Wav2Vec2Processor.from_pretrained(
            "lighteternal/wav2vec2-large-xlsr-53-greek",
            cache_dir="/app/models/wav2vec2"
        )
        
        model = Wav2Vec2ForCTC.from_pretrained(
            "lighteternal/wav2vec2-large-xlsr-53-greek",
            cache_dir="/app/models/wav2vec2"
        ).to(device)
        
        logger.info(f"✅ wav2vec2 Greek model ready on {device.upper()}")
        
        # Check GPU memory usage after model loading
        if device == "cuda":
            # Force GPU memory sync
            torch.cuda.synchronize()
            
            # Get current memory usage
            current_allocated = torch.cuda.memory_allocated() / 1024**3
            current_reserved = torch.cuda.memory_reserved() / 1024**3
            
            logger.info(f"📊 GPU Memory Status:")
            logger.info(f"   - PyTorch allocated: {current_allocated:.2f}GB")
            logger.info(f"   - PyTorch reserved: {current_reserved:.2f}GB")
            logger.info(f"   - Available for use: {allocated_memory - current_reserved:.2f}GB")
            
            # wav2vec2 uses PyTorch directly so this should show actual usage
            logger.info(f"ℹ️  wav2vec2 uses PyTorch directly for GPU memory management")
        
        app.state.wav2vec2_processor = processor
        app.state.wav2vec2_model = model
        app.state.device = device
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize wav2vec2 model: {e}")
        logger.info("⚠️  Model will be loaded on first request")
        app.state.wav2vec2_processor = None
        app.state.wav2vec2_model = None
        app.state.device = "cpu"
    
    yield
    
    logger.info("Shutting down GreekSTT wav2vec2 Service")


app = FastAPI(
    title="GreekSTT wav2vec2 Service",
    description="Academic wav2vec2 service for Greek language research",
    version="1.0.0-wav2vec2",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcription_router)


@app.get("/")
async def root():
    """Root endpoint - returns service information and available endpoints"""
    return JSONResponse(content={
        "service": "GreekSTT wav2vec2 Service",
        "version": "1.0.0-wav2vec2",
        "description": "Academic wav2vec2 service for Greek language research",
        "models": ["wav2vec2-large-xlsr-53-greek"],
        "library": "transformers + PyTorch",
        "endpoints": {
            "transcribe": "/api/v1/transcribe",
            "health": "/api/v1/health"
        }
    })


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler - catches and logs all unhandled exceptions"""
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
        port=8002,
        reload=True,
        log_level="info"
    )