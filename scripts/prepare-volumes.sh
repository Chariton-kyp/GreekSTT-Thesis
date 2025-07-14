#!/bin/bash
# Prepare volume directories for fast model loading

echo "🚀 Preparing volume directories for fast model loading..."

# Create volume directories
echo "📁 Creating volume directories..."
mkdir -p ./ai_models/krikri-4bit
mkdir -p ./ai_models/transformers_cache
mkdir -p ./ai_models/hf_home
mkdir -p ./krikri_cache
mkdir -p ./transformers_cache

# Set permissions for Docker access
echo "🔧 Setting permissions..."
chmod -R 777 ./ai_models
chmod -R 777 ./krikri_cache
chmod -R 777 ./transformers_cache

# Create .gitignore to exclude model files
echo "📝 Creating .gitignore for model directories..."
cat > ./ai_models/.gitignore << 'EOF'
# Ignore all model files
*
!.gitignore
EOF

cat > ./krikri_cache/.gitignore << 'EOF'
# Ignore all cache files
*
!.gitignore
EOF

cat > ./transformers_cache/.gitignore << 'EOF'
# Ignore all cache files
*
!.gitignore
EOF

echo "✅ Volume directories prepared successfully!"
echo ""
echo "📊 Directory structure:"
echo "  ./ai_models/          - Main model storage"
echo "  ./ai_models/krikri-4bit/ - Pre-quantized Krikri models"
echo "  ./krikri_cache/       - Krikri-specific cache"
echo "  ./transformers_cache/ - HuggingFace cache"
echo ""
echo "💡 Next steps:"
echo "  1. Run: docker-compose up -d"
echo "  2. Run: docker-compose exec ai python /app/scripts/prepare-krikri-fast.py"
echo "  3. Models will be ready for fast 20-30 second loading!"