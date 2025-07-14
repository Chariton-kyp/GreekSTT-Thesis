# 🎓 GreekSTT Research Platform

## Academic ASR Model Comparison Platform for Greek Language

> **ΣΗΜΑΝΤΙΚΟ**: Αυτό είναο academic version του project για διπλωματική εργασία.
> **IMPORTANT**: This is the academic version for Master's thesis research.

## 🎯 Thesis Objective

**Title**: "Comparative Performance Analysis of Modern ASR Models on Greek Language: Microservices Architecture and Optimization Study"

**Research Focus**: Development and evaluation of a model comparison system for automatic recognition of Greek speech using microservices architecture.

**Academic Institution**: Τμήμα Πληροφορικής - Πανεπιστήμιο Πειραιώς  
**Author**: Chariton Kypraios  
**Degree**: Master of Science in Informatics
**Year**: 2025

## 🏗️ Academic System Architecture

```
┌─────────────┐     ┌─────────────────────────────────────┐
│   Frontend  │────►│        Backend API (Flask)          │
│  (Angular)  │     │      (Research Orchestration)       │
└─────────────┘     └─────────────────┬───────────────────┘
                                      │
                                      │ (Academic Comparison)
                                      ▼
                    ┌─────────────────────────────────────┐
                    │    AI Microservice (FastAPI)        │
                    │    (Individual Model Comparison)    │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────┴───────────────────┐
                    │                                     │
          ┌─────────▼─────────┐              ┌────────────▼────────────┐
          │ Whisper-large-v3  │              │   wav2vec2-greek        │
          │ (Model A)         │              │   (Model B)             │
          └───────────────────┘              └─────────────────────────┘
                                     │
                               ┌─────▼─────┐
                               │Research   │
                               │Analytics  │
                               └───────────┘
```

## 🔬 Research Contributions

### 1. Systematic Model Comparison for Greek Language

- First comprehensive comparison Whisper vs wav2vec2 for Greek
- Performance analysis across domains (medical, legal, news)
- Greek-specific optimization evaluation

### 2. Academic Microservices Architecture

- Clean separation of research concerns
- Scalable comparison pipeline design
- Academic-focused patterns and methodologies

### 3. Greek Language Research Framework

- Phonetic preprocessing for Greek language specifics
- Medical terminology handling and optimization
- Accent and diacritic restoration algorithms
- Comprehensive evaluation methodology

## 🚀 Quick Academic Setup

### Prerequisites for Research

- Node.js 22+ (for frontend development)
- Python 3.11+ (for backend and AI services)
- Docker & Docker Compose (for infrastructure)
- GPU recommended (auto-fallback to CPU supported)

### Academic Platform Setup

**No API credentials required for basic operation!**

#### Core Research Features (No Setup Required)

✅ **Whisper large-v3** - Works immediately, no token needed  
✅ **wav2vec2 Greek** - Works immediately, no token needed  
✅ **Model Comparison** - Full functionality available  
✅ **Performance Analytics** - Complete academic metrics  
✅ **Email System Demo** - MailHog integration included

#### Optional Advanced Features

🔹 **HuggingFace Token** (Optional - only for speaker diarization)

- Get free token at [HuggingFace](https://huggingface.co/settings/tokens)
- Add to `.env`: `HUGGINGFACE_TOKEN=your_token_here`
- Enables "who spoke when" analysis (not needed for basic research)

#### Authentication System

🔐 **Email/Password Authentication** - Complete registration and login system  
📧 **Email Verification** - Real 6-digit codes via MailHog (localhost:8025)  
🎓 **Academic Registration** - Professional user accounts for research

**Email System:** Users register normally and receive verification emails in MailHog (perfect for thesis demonstrations!)

### 🛡️ Repository Security

**Safe for Public Sharing:**

- ✅ **No sensitive data** committed to repository
- ✅ **Simple HTTP configuration** (no certificate management required)
- ✅ **Environment variables** use template with placeholders
- ✅ **Admin credentials** configurable via environment variables
- ✅ **Business secrets protected** - no proprietary ensemble algorithms

**What's automatically excluded from repository:**

- `.env` files with real secrets (only `.env.example` template included)
- SSL configurations (removed for thesis simplification)
- Any proprietary ensemble/combination algorithms (academic comparison only)

### Quick Start (3 Commands)

```bash
# 1. Install dependencies
npm install

# 2. Setup environment (copy .env.example to .env)
cp .env.example .env

# 3. Complete setup and start platform
npm run setup

# Access: http://localhost:4200
# Email Demo: http://localhost:8025
```

### 🔐 Security Information

**Academic Development Security:**

- ✅ **HTTP-only configuration** for simplified thesis demonstration
- ✅ **No certificate management** required for academic presentations
- ✅ **Easy setup** without SSL complexity
- ✅ **Academic appropriate** for research demonstrations

### Alternative Development Setup

```bash
# Hybrid development (frontend local, services in Docker)
npm run dev:infra       # Start infrastructure
npm run dev:backend     # Start backend API
npm run dev:ai          # Start AI service
npm run dev:frontend    # Start frontend with hot-reload

# Access points:
# Frontend: http://localhost:4200
# Backend API: http://localhost:5001
# AI Service: http://localhost:8000
# Email Demo: http://localhost:8025
```

### Manual Step-by-Step Setup

```bash
# 1. Clone and setup
git clone https://github.com/Chariton-kyp/GreekSTT-Thesis.git
cd GreekSTT-Thesis

# 2. Install dependencies
npm install

# 3. Setup environment
cp .env.example .env
# Configure with your academic settings

# 4. Start infrastructure
npm run dev:infra     # Database, Redis, MailHog

# 5. Start services
npm run dev:backend   # Flask API
npm run dev:ai        # AI comparison service
npm run dev:frontend  # Angular research interface
```

## 📊 Research Evaluation Metrics

### Primary Metrics

- **Word Error Rate (WER)**: Primary accuracy metric for transcription quality
- **Character Error Rate (CER)**: Character-level accuracy measurement
- **Real-time Factor (RTF)**: Processing speed compared to audio duration
- **Memory Usage**: GPU/CPU resource consumption analysis

### Greek-Specific Metrics

- **Diacritic Accuracy**: Proper handling of Greek accent marks
- **Morphology Correctness**: Greek word form recognition
- **Phonetic Precision**: Greek phoneme recognition accuracy
- **Domain Performance**: Accuracy across medical, legal, news domains

### Comparison Analytics

- **Relative Performance**: Head-to-head model comparison
- **Speed-Accuracy Trade-offs**: Performance vs processing time analysis
- **Resource Efficiency**: Memory and computational requirements
- **Greek Language Optimization**: Language-specific improvements

## 🎓 Academic Demo Capabilities

### Individual Model Processing

1. **Whisper-Only Processing**: Large-v3 model for Greek transcription
2. **wav2vec2-Only Processing**: Greek-optimized wav2vec2 model
3. **Model-Specific Analytics**: Individual performance metrics

### Comparison Analysis

1. **Side-by-Side Comparison**: Direct model performance comparison
2. **Performance Metrics Dashboard**: Visual analytics interface
3. **Greek Text Optimization**: Post-processing demonstrations
4. **Research Insights**: Academic analysis and recommendations

### Supporting Systems

1. **Email System Demo**: Complete authentication flow with MailHog
2. **Performance Benchmarking**: Automated speed and accuracy testing
3. **Data Export**: Research data export for thesis analysis

## 📚 Academic Documentation

### Research Documentation

- [Installation Guide](docs/academic/INSTALLATION.md) - Complete setup instructions
- [API Reference](docs/academic/API-REFERENCE.md) - Research endpoint documentation
- [Architecture Guide](docs/academic/ARCHITECTURE.md) - System design for thesis
- [Demo Guide](docs/academic/DEMO-GUIDE.md) - Committee presentation protocol

### Implementation Documentation

- [Frontend Documentation](apps/frontend/README.md) - Angular research interface
- [Backend Documentation](apps/backend/README.md) - Flask API architecture
- [AI Service Documentation](apps/ai-service/README.md) - Model comparison service

## 🎯 System Access Points

### Development URLs

- **Frontend**: http://localhost:4200 (Academic research interface)
- **Backend API**: http://localhost:5001 (Research API documentation)
- **AI Service**: http://localhost:8000 (Model comparison service)
- **Email Demo**: http://localhost:8025 (MailHog demonstration)
- **Database**: localhost:5432 (Academic research data)
- **PgAdmin**: http://localhost:5050 (admin@greekstt-research.local/admin)

### Academic Configuration

All services configured for academic research use:

- Non-commercial licensing enforced
- Research data isolation and security
- Demo email system (no external dependencies)
- Greek language optimization throughout

## 🗄️ Database Access & Management

### Default Academic Database Setup

**Database Information:**

- **Database Name**: `greekstt-research` (with hyphen)
- **Host**: localhost
- **Port**: 5432
- **Username**: postgres
- **Password**: postgres

### Pre-seeded Academic Data

The system automatically creates academic test data on first startup:

**Demo Account:**

Register a new account using any academic email address to access the platform.

### Database Tools Access

#### PgAdmin (Web Interface)

- **URL**: http://localhost:5050
- **Email**: admin@greekstt.research
- **Password**: admin
- **Use**: Web-based database management for academic research

#### DBeaver (Desktop Client)

Connect with these settings:

- **Database Type**: PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Database**: `greekstt-research` ⚠️ **Important**: Use hyphen, not underscore
- **Username**: postgres
- **Password**: postgres

#### Command Line Access

```bash
# Access PostgreSQL directly
npm run db:shell

# Or via Docker
docker-compose exec db psql -U postgres -d greekstt-research

# Database management commands
npm run db:migrate    # Run database migrations
npm run db:seed      # Seed academic test data
npm run db:reset     # Reset database (WARNING: destroys all data)
```

### Academic Database Schema

The database includes tables for:

- **Audio Files**: Research audio sample storage
- **Transcriptions**: ASR model output storage
- **Audit Logs**: Academic research activity tracking
- **Email System**: Academic email verification and management

### 🔐 Credential Configuration

**Admin Account Setup (Configurable):**

```bash
# Set custom admin credentials via environment variables:
export ADMIN_EMAIL='your@academic.email'
export ADMIN_PASSWORD='your_secure_password'

export ADMIN_USERNAME='your_admin_username'

# Then run database seeding
npm run db:seed
```

**Default Academic Credentials (if not configured):**

- Email: `admin@greekstt-research.local`
- Password: `academic123`
- Username: `admin`

**Security Note:** The admin seeding script now uses environment variables instead of hardcoded credentials for better security.

### Research Data Structure

**For Thesis Analysis:**

- All ASR results stored with timestamps and model metadata
- Performance metrics automatically calculated and stored
- Comparison data readily available for statistical analysis
- Academic user activity tracked for research validation

**Data Export for Thesis:**

```bash
# Export research data for analysis
npm run export:thesis-data

# Export specific model performance data
docker-compose exec db psql -U postgres -d greekstt-research -c "
  SELECT
    t.id,
    t.audio_duration,
    t.processing_time,
    t.model_used,
    t.accuracy_wer,
    t.accuracy_cer,
    t.created_at
  FROM transcriptions t
  ORDER BY t.created_at DESC;
" --csv > thesis_data.csv
```

## 🔧 Available Academic Commands

### Research Setup

```bash
npm run academic:setup        # Complete academic environment setup
npm run academic:start        # Start all research services
npm run academic:test         # Run integration tests
npm run academic:benchmark    # Performance benchmarking
npm run academic:demo         # Demonstration mode
```

### Development Commands

```bash
npm run dev:infra            # Start database, Redis, MailHog
npm run dev:backend          # Start Flask research API
npm run dev:ai               # Start AI comparison service
npm run dev:frontend         # Start Angular research interface
npm run dev:all              # Start all services concurrently
```

### Research Utilities

```bash
npm run health               # Check all services status
npm run test:integration     # Run academic integration tests
npm run benchmark:models     # Model performance benchmarking
npm run export:thesis-data   # Export research data for analysis
```

## 🧪 Testing and Validation

### Academic Integration Testing

```bash
npm run test:academic        # Full academic platform testing
npm run test:models          # Individual model testing
npm run test:comparison      # Model comparison testing
npm run test:demo           # Demo scenario validation
```

### Research Validation

- Individual model processing verification
- Comparison accuracy validation
- Performance metrics verification
- Email system demonstration testing
- Greek language optimization testing

## 🎨 Academic Interface Features

### Research Dashboard

- Model performance comparison charts
- Greek language accuracy metrics
- Processing speed analytics
- Memory usage monitoring
- Academic insights and recommendations

### Model Comparison Interface

- Individual model selection (Whisper/wav2vec2)
- Side-by-side comparison mode
- Real-time performance metrics
- Greek text optimization display
- Research data export functionality

### Email System Demo

- Academic user registration flow
- Email verification with MailHog
- Greek language email templates
- Non-commercial academic disclaimers

## 📄 License

**NON-COMMERCIAL ACADEMIC RESEARCH LICENSE**

This software is licensed for academic research, educational, and non-commercial purposes only.

### ✅ Permitted Uses:

- Academic research and study
- Educational purposes in universities
- Personal learning and experimentation
- Non-profit research activities
- Thesis and dissertation work
- Scientific publications

### ❌ Prohibited Uses:

- Commercial use of any kind
- Integration into commercial products
- Selling or monetizing the software
- Use by for-profit companies
- Distribution in commercial packages

---

## 🏛️ Academic Context

This research platform was developed as part of a Master's thesis in Computer Science, focusing on the comparative analysis of modern ASR models for Greek language processing. The system demonstrates:

- **Microservices Architecture**: Scalable, maintainable system design
- **Greek Language Optimization**: Specialized processing for Greek linguistic features
- **Model Comparison Methodology**: Systematic evaluation framework
- **Academic Standards**: Research-focused implementation and documentation

The platform serves as both a functional demonstration of ASR technology and a comprehensive research tool for Greek language speech recognition analysis.

---

Copyright (c) 2025 Chariton Kypraios  
Academic Research License - See LICENSE file for details
