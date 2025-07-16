"""
Simple Device Detection for Academic Research
"""
import logging

logger = logging.getLogger(__name__)


def detect_device() -> str:
    """Simple device detection"""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("✅ CUDA available - using GPU")
            return "cuda"
        else:
            logger.info("ℹ️ CUDA not available - using CPU")
            return "cpu"
    except ImportError:
        logger.info("ℹ️ PyTorch not available - using CPU")
        return "cpu"


def get_device_info() -> dict:
    """Get device information"""
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            return {
                "device": "cuda",
                "name": torch.cuda.get_device_name(device),
                "memory_total": torch.cuda.get_device_properties(device).total_memory / (1024**3),
                "memory_allocated": torch.cuda.memory_allocated(device) / (1024**3),
                "memory_free": (torch.cuda.get_device_properties(device).total_memory - torch.cuda.memory_allocated(device)) / (1024**3)
            }
        else:
            return {
                "device": "cpu",
                "name": "CPU",
                "memory_total": 0,
                "memory_allocated": 0,
                "memory_free": 0
            }
    except ImportError:
        return {
            "device": "cpu",
            "name": "CPU",
            "memory_total": 0,
            "memory_allocated": 0,
            "memory_free": 0
        }