# GreekSTT Research Platform

> Academic Research Platform for Comparative Analysis of Greek ASR Models  
> Master's Thesis - Department of Computer Science, University of Piraeus

## Overview

This platform implements a comparative analysis system for the two most powerful open-source ASR models for Greek language: **Whisper-large-v3** (OpenAI) and **wav2vec2-greek** (Facebook). The dual objective was to develop a modern microservices architecture while conducting systematic performance evaluation of ASR models on Greek speech.

## Key Research Findings

- **No single model achieves >90% accuracy on Greek without fine-tuning**
- Whisper-large-v3 shows better general-purpose performance but requires significant resources
- wav2vec2-greek excels in specific domains due to Greek corpus pre-training
- Both models struggle with Greek diacritics and domain-specific terminology

## Architecture

```
Frontend (Angular 19) → Backend API (Flask) → AI Service (FastAPI)
                                                    ↓
                                            Whisper | wav2vec2
```

### Microservices Benefits for ASR Comparison
- **Independent Model Processing**: Each model runs in isolation, preventing interference
- **Fair Resource Allocation**: GPU memory managed separately per model
- **Scalable Comparison**: Can add new models without architectural changes
- **Real-time Analysis**: WebSocket updates for live transcription progress

## Technical Stack

- **Frontend**: Angular 19, TypeScript, PrimeNG, Chart.js
- **Backend**: Flask, PostgreSQL, Redis, JWT Auth, WebSocket
- **AI Service**: FastAPI, PyTorch, CUDA, faster-whisper
- **Infrastructure**: Docker Compose, Microservices, Nx Monorepo

## System Requirements

### Minimum GPU Requirements
- **VRAM**: 6-7GB minimum (with quantized models)
- **CUDA**: 11.8+ with cuDNN 8.x
- **Note**: CPU fallback available but significantly slower

### Development Machine Specifications
- **CPU**: Intel i9-14900HX
- **GPU**: NVIDIA RTX 4080 Mobile 12GB
- **RAM**: 64GB DDR5 5600MHz
- **Storage**: 2TB NVMe SSD

## Installation

```bash
# Clone repository
git clone https://github.com/Chariton-kyp/GreekSTT-Thesis.git
cd GreekSTT-Thesis

# Install dependencies
npm install

# Setup environment
cp .env.example .env

# Start platform
npm run setup && npm run docker:up
```

Access: http://localhost:4200

## Model Performance Insights

### Whisper-large-v3
- General-purpose multilingual model
- Better context understanding
- Higher resource consumption (4-5GB VRAM)
- Processing time: ~10% of audio duration on GPU

### wav2vec2-greek
- Pre-trained on Greek speech corpus
- Faster inference (2-3GB VRAM)
- Better for specific Greek domains
- Processing time: ~5% of audio duration on GPU

## Research Methodology

The platform enables systematic comparison through:
- Side-by-side transcription analysis
- WER/CER metrics calculation
- Processing time benchmarking
- Memory usage profiling
- Greek-specific accuracy metrics (diacritics, morphology)

## Academic Resources & References

### Model Sources
- **Whisper**: OpenAI research papers and model weights
- **wav2vec2**: Facebook AI Research, Greek fine-tuning by lighteternal

### Knowledge Base
- University of Piraeus coursework in AI/ML and Software Engineering
- Professional experience in production system development
- Greek NLP research papers and linguistic resources
- Mozilla Common Voice Greek dataset for testing

## License & Usage Restrictions

**ACADEMIC RESEARCH LICENSE - NON-COMMERCIAL USE ONLY**

This software is strictly for academic research and educational purposes.

### Prohibited Uses
- Commercial deployment or monetization
- Integration into commercial products/services
- Resale or redistribution for profit
- Use by commercial entities

### Permitted Uses
- Academic research and thesis work
- Educational purposes in universities
- Personal learning and experimentation
- Scientific publications with attribution

## Author

**Chariton Kypraios**  
MSc Student - Department of Computer Science  
University of Piraeus  
Email: haritos19@gmail.com

## Acknowledgments

- OpenAI for Whisper model and research
- Facebook AI Research for wav2vec2 architecture
- University of Piraeus for academic guidance
- Mozilla Common Voice for Greek speech dataset

---

Copyright © 2025 Chariton Kypraios - Academic Research License