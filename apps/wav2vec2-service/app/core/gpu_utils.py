"""GPU memory monitoring utilities for wav2vec2 service"""
import torch
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GPUMemoryMonitor:
    """Monitor GPU memory usage"""
    
    def __init__(self):
        self.device_available = torch.cuda.is_available()
        if self.device_available:
            self.device = torch.cuda.current_device()
            self.device_name = torch.cuda.get_device_name(self.device)
            self.total_memory = torch.cuda.get_device_properties(self.device).total_memory / (1024**3)
        else:
            self.device = None
            self.device_name = "CPU"
            self.total_memory = 0
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        return {
            "available": self.device_available,
            "name": self.device_name,
            "total_memory": self.total_memory
        }
    
    def get_gpu_memory_info(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        if not self.device_available:
            return {
                "total": 0,
                "allocated": 0,
                "free": 0,
                "reserved": 0
            }
        
        allocated = torch.cuda.memory_allocated(self.device) / (1024**3)
        reserved = torch.cuda.memory_reserved(self.device) / (1024**3)
        free = self.total_memory - allocated
        
        return {
            "total": self.total_memory,
            "allocated": allocated,
            "free": free,
            "reserved": reserved
        }
    
    def get_available_memory(self) -> float:
        """Get available GPU memory in GB"""
        if not self.device_available:
            return 0
        
        info = self.get_gpu_memory_info()
        return info["free"]
    
    def log_memory_status(self, service_name: str = "Service") -> None:
        """Log detailed memory status"""
        if not self.device_available:
            logger.info(f"📊 {service_name} Memory Status: CPU mode")
            return
        
        torch.cuda.synchronize()
        info = self.get_gpu_memory_info()
        
        logger.info(f"📊 {service_name} Memory Status:")
        logger.info(f"   - Total GPU: {info['total']:.2f}GB")
        logger.info(f"   - Allocated: {info['allocated']:.2f}GB")
        logger.info(f"   - Reserved: {info['reserved']:.2f}GB")
        logger.info(f"   - Free: {info['free']:.2f}GB")
        logger.info(f"   - Usage: {(info['allocated']/info['total']*100):.1f}%")