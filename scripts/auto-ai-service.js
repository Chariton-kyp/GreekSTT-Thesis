#!/usr/bin/env node

/**
 * Auto AI Service Selector
 * Automatically chooses GPU or CPU based on system capabilities
 */

const { execSync, spawn } = require('child_process');
const os = require('os');

function isGpuAvailable() {
    try {
        // Check for NVIDIA GPU on Linux/WSL
        if (os.platform() === 'linux' || os.platform() === 'win32') {
            execSync('nvidia-smi', { stdio: 'ignore' });
            console.log('🚀 GPU detected - using AI service with GPU support');
            return true;
        }
    } catch (error) {
        // GPU not available or command failed
    }
    
    console.log('💻 No GPU detected - using AI service with CPU only');
    return false;
}

function startAiService() {
    const hasGpu = isGpuAvailable();
    const service = 'ai'; // Always use 'ai' service - GPU/CPU handled by Docker runtime
    
    console.log(`Starting AI service: ${service} ${hasGpu ? '(with GPU support)' : '(CPU only)'}`);
    
    // Start the appropriate service
    const command = 'docker-compose';
    const args = [
        '-f', 'docker-compose.yml', 
        '-f', 'docker-compose.dev.yml', 
        'up', service
    ];
    
    const child = spawn(command, args, {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('error', (error) => {
        console.error('❌ Failed to start AI service:', error.message);
        process.exit(1);
    });
    
    child.on('exit', (code) => {
        console.log(`🔄 AI service ${service} exited with code ${code}`);
        process.exit(code);
    });
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🔄 Gracefully shutting down AI service...');
        child.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        console.log('\n🔄 Gracefully shutting down AI service...');
        child.kill('SIGTERM');
    });
}

// Start the service
startAiService();