# GreekSTT Comparison Platform

> **Academic Comparison Platform for Comparative Analysis of Greek ASR Models**  
> Master's Thesis - Department of Computer Science, University of Piraeus  
> **Systematic Evaluation of Whisper vs wav2vec2 for Greek Language Processing**

---

## Table of Contents

- [Platform Overview](#platform-overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Development Workflow](#development-workflow)
- [Performance Analysis](#performance-analysis)
- [Comparison Methodology](#comparison-methodology)
- [Troubleshooting](#troubleshooting)
- [Technical Resources](#technical-resources)
- [License & Usage](#license--usage)

---

## Platform Overview

### Objective

This platform implements a comprehensive comparative analysis system for the two most powerful open-source ASR models for Greek language: **Whisper-large-v3** (OpenAI) and **wav2vec2-greek** (Facebook/lighteternal). The platform addresses the need for systematic evaluation of modern ASR technologies for morphologically complex languages.

### Key Contributions

1. **Comparative Analysis Framework**: First systematic comparison of Whisper vs wav2vec2 for Greek ASR
2. **Greek Language Optimization**: Comprehensive diacritic and morphology handling implementation
3. **Microservices Architecture**: Scalable design enabling fair, independent model comparison
4. **Performance Benchmarking**: Real-world performance metrics on authentic Greek audio content
5. **Complete Platform**: Full-featured tool with export capabilities for further analysis

### Key Findings

- **Whisper-large-v3**: clearly more robust than wav2vec2-greek on the real-world audio tested (in a demonstration on one YouTube video: WER 2.5% vs 61.4%, see "Demonstration results" below), but more resource-intensive
- **wav2vec2-greek**: faster and lighter (greedy CTC), but degrades sharply on noisy, multi-speaker or out-of-domain content
- **Greek Language Challenges**: Both models struggle with diacritics, morphological complexity, and dialectal variations
- **Resource Requirements**: GPU acceleration essential for practical deployment

---

## Quick Start

### Immediate Setup (3 Commands)

```bash
# 1. Clone and navigate
git clone https://github.com/Chariton-kyp/GreekSTT-Thesis.git
cd GreekSTT-Thesis

# 2. Setup dependencies and environment
npm install && cp .env.example .env && npm run setup

# 3. Start complete platform
npm run docker:up
```

**Access Points:**
- **Main Interface**: http://localhost:4200
- **Admin Account**: admin@admin.gr / admin123

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Angular 19 Frontend                           │
│        Comparison UI + Real-time WebSocket + Charts               │
│                     Port: 4200                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP API + WebSocket
                ┌────────▼─────────┐
                │  Flask Backend   │
                │ Backend API     │
                │ JWT + SocketIO   │
                │   Port: 5001     │
                └─────────┬────────┘
                          │ Independent HTTP Calls
            ┌─────────────┴──────────────┐
            │                            │
    ┌───────▼─────────┐         ┌───────▼──────────┐
    │ Whisper Service │         │ wav2vec2 Service │
    │ OpenAI Model    │         │ Greek Specialized│
    │   Port: 8001    │         │   Port: 8002     │
    │ GPU: 60% (7.2GB)│         │ GPU: 40% (4.8GB) │
    └─────────────────┘         └──────────────────┘
```

### Microservices Benefits for ASR Comparison

- **Independent Model Processing**: Each model operates in isolation, preventing interference
- **Fair Resource Allocation**: GPU memory partitioned (60% Whisper, 40% wav2vec2)
- **Scalable Comparison**: Architecture supports additional models without modification
- **Real-time Analysis**: WebSocket integration for live transcription progress
- **Comparison Integrity**: No ensemble logic - pure individual model evaluation

### Technical Stack

- **Frontend**: Angular 19, TypeScript, PrimeNG, Chart.js, WebSocket Client
- **Backend**: Flask, PostgreSQL, Redis, JWT Authentication, SocketIO
- **AI Services**: FastAPI, PyTorch, CUDA, faster-whisper, transformers
- **Infrastructure**: Docker Compose, Nx Monorepo, NVIDIA Container Toolkit
- **Database**: PostgreSQL 16, Redis 7, MailHog (email demo), PgAdmin

---

## Installation

### System Requirements

#### Hardware Requirements
| Component | Minimum | Recommended | Development Machine |
|-----------|---------|-------------|-------------------|
| **GPU** | GTX 1660 (6GB VRAM) | RTX 4070 (12GB VRAM) | RTX 4080 Mobile (12GB) |
| **CPU** | 4-core Intel/AMD | 8-core Intel/AMD | Intel i9-14900HX |
| **RAM** | 16GB | 32GB | 64GB DDR5-5600 |
| **Storage** | 50GB SSD | 100GB NVMe | 2TB NVMe SSD |
| **CUDA** | 11.8+ | 12.1+ | 12.1 |

#### Software Dependencies
```bash
# Required Software
Node.js: ^22.16.0
Python: 3.11+
Docker: 20.10+
Docker Compose: 2.0+
NVIDIA Container Toolkit: latest
```

### Complete Installation Process

```bash
# 1. Clone Repository
git clone https://github.com/Chariton-kyp/GreekSTT-Thesis.git
cd GreekSTT-Thesis

# 2. Install Node.js Dependencies
npm install

# 3. Build Shared Libraries
npm run build:libs

# 4. Environment Setup
cp .env.example .env
# Edit .env with your settings (optional - defaults work for development)

# 5. Complete Platform Setup
npm run setup  # Installs deps, builds libs, starts infrastructure, migrates DB

# 6. Start All Services
npm run docker:up
```

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Main Interface** | http://localhost:4200 | Main application UI |
| **Backend API** | http://localhost:5001 | Flask API + Swagger docs |
| **Whisper Service** | http://localhost:8001 | FastAPI Whisper endpoint |
| **wav2vec2 Service** | http://localhost:8002 | FastAPI wav2vec2 endpoint |
| **Email Demo** | http://localhost:8025 | MailHog verification demo |
| **Database Admin** | http://localhost:5050 | PgAdmin (admin@greekstt.research/admin) |

---

## Development Workflow

### Development Mode (Hot Reload)

```bash
# Start infrastructure only
npm run dev:infra  # PostgreSQL, Redis, MailHog

# Start individual services with hot reload
npm run dev:backend    # Flask API (debugpy: 5678)
npm run dev:whisper    # Whisper service (debugpy: 5680)
npm run dev:wav2vec2   # wav2vec2 service (debugpy: 5681)
npm run dev:frontend   # Angular (hot-reload: 4200)

# Or start all development services at once
npm run dev:all
```

### Database Operations

```bash
# Database management
npm run db:migrate     # Apply schema migrations
npm run db:seed        # Load demo data (admin@admin.gr/admin123)
npm run db:shell       # Direct PostgreSQL access
npm run db:backup      # Create timestamped backup
npm run db:restore --file=backup.sql  # Restore from backup
```

### Health Monitoring

```bash
# Check all services
npm run health:all

# Individual service checks
curl http://localhost:4200           # Frontend
curl http://localhost:5001/api/health    # Backend
curl http://localhost:8001/health        # Whisper
curl http://localhost:8002/health        # wav2vec2
```

---

## Performance Analysis

### Demonstration results (not a benchmark)

**Test Environment**: RTX 4080 Mobile (12GB), Intel i9-14900HX, 64GB RAM

The platform compares models on user-supplied audio against a user-supplied reference; it does not include a fixed evaluation dataset. The figures below come from the thesis demonstration (§7.6.2) on **one YouTube video** scored through the platform. They illustrate the workflow and are not a statistically meaningful benchmark. They were also computed with the normalizer affected by the issue described under "Known issues and errata", so they are not comparable with published Greek WER figures.

| Metric (single video, n = 1) | Whisper-large-v3 | wav2vec2-greek |
|---|---:|---:|
| WER | 2.5% | 61.4% |
| CER | 1.3% | 39.9% |
| Speed (thesis §9.4, approx.) | ~7x real time | ~16x real time |
| VRAM (approx.) | 4-5 GB | 2-3 GB |

### Model Characteristics

#### Whisper-large-v3
- **Strengths**: General-purpose multilingual model, superior context understanding, robust noise handling
- **Greek Performance**: Excellent for diverse content types, handles code-switching well
- **Resource Requirements**: 4-5GB VRAM, higher CPU usage
- **Best Use Cases**: Mixed content, noisy environments, multilingual speech

#### wav2vec2-greek
- **Strengths**: Pre-trained on Greek corpus, faster inference, efficient resource usage
- **Greek Performance**: Excellent for domain-specific content, superior morphology recognition
- **Resource Requirements**: 2-3GB VRAM, efficient processing
- **Best Use Cases**: Clean Greek speech, domain-specific content, resource-constrained environments

### Greek Language Optimizations

- **Unicode NFC Normalization**: Proper handling of Greek character combinations
- **Diacritic Processing**: Specialized accent mark handling (ά, έ, ή, ί, ό, ύ, ώ)
- **Morphological Analysis**: Word form recognition and inflection processing
- **Domain Adaptation**: Performance varies significantly by content domain

---

## Comparison Methodology

### Comparative Analysis Framework

1. **Independent Processing**: Each model processes identical audio independently
2. **Resource Allocation**: GPU memory fractions configured per service (60/40). In comparison mode both models run concurrently on the same GPU, so timings are measured under contention, and the fraction is not enforced for faster-whisper (CTranslate2)
3. **Systematic Evaluation**: Standardized metrics (WER, CER, processing time)
4. **Real-world Testing**: Diverse audio sources (studio, YouTube, live recordings)
5. **Greek-specific Analysis**: Greek text normalization and diacritic analysis (see "Known issues and errata")

### Evaluation Metrics

- **Word Error Rate (WER)**: Industry-standard transcription accuracy measure
- **Character Error Rate (CER)**: Fine-grained accuracy at character level
- **Processing Time**: Real-time factor calculation for efficiency analysis
- **Resource Usage**: GPU memory, CPU utilization profiling
- **Greek-specific Analysis**: Diacritic handling (see "Known issues and errata")

### Test Data Sources

- **Studio Recordings**: High-quality controlled environment speech
- **YouTube Content**: Real-world varied quality audio
- **Live Recordings**: Direct microphone input via WebRTC
- **Academic Content**: University lectures and presentations

---

## Troubleshooting

### Common Issues

#### Docker Services Won't Start
```bash
# Check port conflicts
npm run debug:check-ports

# Reset Docker state
npm run docker:clean && npm run docker:up

# Check Docker logs
npm run docker:logs
```

#### GPU Not Detected
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Check NVIDIA Container Toolkit
docker info | grep nvidia

# Install NVIDIA Container Toolkit (Ubuntu)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

#### Frontend Build Errors
```bash
# Clear cache and rebuild
npm run clean && npm install
npm run build:libs

# Check Node.js version
node --version  # Should be ^22.16.0
```

#### Database Connection Issues
```bash
# Reset database completely
npm run db:destroy-all  # ⚠️ DESTROYS ALL DATA
npm run docker:up
npm run db:migrate
npm run db:seed
```

#### Model Download Problems
```bash
# Manual model download
docker-compose exec whisper-service python -c "
from faster_whisper import WhisperModel
model = WhisperModel('large-v3', download_root='/app/models/whisper')
"

docker-compose exec wav2vec2-service python -c "
from transformers import Wav2Vec2ForCTC
model = Wav2Vec2ForCTC.from_pretrained('lighteternal/wav2vec2-large-xlsr-53-greek')
"
```

#### Performance Issues
```bash
# Reduce GPU memory allocation in .env
GPU_MEMORY_FRACTION_WHISPER=0.4
GPU_MEMORY_FRACTION_WAV2VEC2=0.3

# Check system resources
nvidia-smi
docker stats
```

### Debug Mode

```bash
# Enable verbose logging
export DEBUG_MODE=1
export LOG_LEVEL=DEBUG

# Attach debugger (VS Code)
# Backend: localhost:5678
# Whisper: localhost:5680
# wav2vec2: localhost:5681
```

---

## Technical Resources

### Background & Technical Context

#### Greek ASR Challenges
- **Morphological Complexity**: 25+ inflection patterns per word class
- **Diacritic System**: 7 accent marks affecting meaning and pronunciation
- **Limited Training Data**: Significantly less Greek speech data compared to English
- **Dialectal Variations**: Regional pronunciation differences across Greece and Cyprus
- **Code-switching**: Mixed Greek-English content in modern speech

#### State of the Art
- **Whisper**: Multilingual transformer model trained on 680k hours of audio
- **wav2vec2**: Self-supervised learning with language-specific fine-tuning
- **Greek-specific Work**: Limited development work on modern ASR comparison

#### Implementation Gap
No comprehensive comparison platform of state-of-the-art ASR models on real-world Greek audio with systematic methodology and practical implementation.

### Model Sources & References

- **Whisper**: OpenAI papers and model weights (Apache 2.0 License)
- **wav2vec2-greek**: Facebook AI base + lighteternal Greek fine-tuning
- **Greek Linguistic Resources**: University of Athens NLP work
- **Test Data**: user-supplied recordings

### Technical Validation

- **University of Piraeus**: Academic supervision and methodology review
- **Professional Development**: Industry-standard software engineering practices
- **Open Source**: Complete codebase available for reproducibility
- **Documentation**: Comprehensive technical and user documentation

---

## License & Usage

### Academic Research License

**STRICTLY FOR ACADEMIC AND EDUCATIONAL USE**

#### Permitted Uses ✅
- Academic research and thesis work
- Educational purposes in universities
- Personal learning and experimentation
- Scientific publications with proper attribution
- Non-commercial collaboration

#### Prohibited Uses ❌
- Commercial deployment or monetization
- Integration into commercial products/services
- Resale or redistribution for profit
- Use by commercial entities without explicit permission

### Citation

If you use this work, please cite:

```bibtex
@mastersthesis{kypraios2025greekstt,
  title={Comparative Analysis of ASR Models for the Greek Language: A Microservices Approach},
  author={Kypraios, Chariton},
  year={2025},
  school={University of Piraeus, Department of Informatics},
  type={Master's Thesis},
  url={https://github.com/Chariton-kyp/GreekSTT-Thesis}
}
```

---

## Author & Acknowledgments

### Author
**Chariton Kypraios**  
MSc Student - Department of Informatics 
University of Piraeus  
📧 haritos19@gmail.com  
🔗 [GitHub](https://github.com/Chariton-kyp)

### Acknowledgments

- **OpenAI** for Whisper model and transformer research
- **Facebook AI Research** for wav2vec2 architecture and self-supervised learning
- **University of Piraeus** for academic guidance and computational resources
- **Mozilla Foundation** for Common Voice Greek dataset
- **lighteternal** for Greek-specific wav2vec2 fine-tuning

## Known issues and errata (October 2026)

A later review of the code found the following. They are documented here rather than silently fixed,
because the thesis results were produced with this code.

1. **The Greek text normalizer drops accented vowels.** `GreekTextNormalizer` keeps only the base Greek
   ranges (U+0391-03A9, U+03B1-03C9, U+1F00-1FFF), so precomposed tonos/diaeresis vowels
   (ά έ ή ί ό ύ ώ ϊ ϋ ΐ ΰ) are replaced by spaces. Words are split into fragments, the reference word
   count is inflated, and WER/CER computed by the platform are not comparable with standard Greek ASR
   scoring. Latin-script tokens are also removed.
2. **Diacritic accuracy always reports 100%**, because the analyzer runs after the normalizer above.
3. **Confidence-based "accuracy" is a heuristic, not a ground-truth metric.** For wav2vec2 it is the
   mean max-softmax confidence clamped to 60-95. Only WER/CER against a reference are ground-truth
   metrics.
4. **`/comparison/detailed` returns fixed demonstration values** (morphology and error-pattern
   figures), not computed results.
5. **`apps/*/app/ai/models/*.py` are not used by the running services.** Live inference is in each
   service's `app/main.py` and `app/api/transcription.py`. Settings in the unused modules, such as the
   hallucination filters, did not run.
6. **Timing.** Processing times come from a single `time.time()` measurement without warm-up. In
   comparison mode both models share the GPU, and the stored per-model times in that mode can be 0
   because of a key mismatch.
7. **No automated tests** cover the metrics, the normalizer or the inference configuration.

A follow-up project applies a held-out benchmark, corpus-level WER with meeting-level confidence
intervals, a validated harness and a controlled timing protocol:
[whisper-meeting-adaptation](https://github.com/Chariton-kyp/whisper-meeting-adaptation).

---

**© 2025 Chariton Kypraios - Academic Research License**  
*This work represents a significant contribution to Greek language ASR comparison and demonstrates the practical application of modern microservices architecture in academic contexts.*