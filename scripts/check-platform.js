#!/usr/bin/env node

/**
 * Platform checker - runs appropriate script based on OS
 */

const { spawn } = require('child_process');
const os = require('os');

function startAllServices() {
    let command, args;
    
    if (os.platform() === 'win32') {
        console.log('🪟 Windows detected - using PowerShell script');
        command = 'npm';
        args = ['run', 'start-all:windows'];
    } else {
        console.log('🐧 Unix/Linux detected - using bash script');
        command = 'npm';
        args = ['run', 'start-all:unix'];
    }
    
    const child = spawn(command, args, {
        stdio: 'inherit',
        shell: true
    });
    
    child.on('error', (error) => {
        console.error('❌ Failed to start services:', error.message);
        process.exit(1);
    });
    
    child.on('exit', (code) => {
        process.exit(code);
    });
}

startAllServices();