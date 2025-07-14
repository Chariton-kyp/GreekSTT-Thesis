import os
import sys

# For now, skip eventlet/gevent to avoid conflicts
# We'll use threading mode which is simpler and more stable
print("🔧 Using threading mode for WebSocket")

from app import create_app

# Get environment from environment variable
flask_env = os.environ.get('FLASK_ENV', 'development')
app, socketio = create_app(flask_env)

if __name__ == "__main__":
    # Backend runs on HTTP only for thesis simplification
    print("🔧 Backend running on HTTP only")
    
    # Check if running under debugpy
    running_under_debugpy = os.environ.get('RUNNING_UNDER_DEBUGPY', 'false').lower() == 'true'
    
    print(f"🚀 Starting Flask backend with SocketIO support")
    print(f"🔧 Environment: {flask_env}")
    print(f"🐞 Running under debugpy: {running_under_debugpy}")
    print(f"🌐 WebSocket support: Enabled")
    
    if running_under_debugpy:
        # When running under debugpy, use a simple approach that avoids reloader conflicts
        print("🔧 Debugpy detected - using debugpy-compatible SocketIO configuration")
        
        # Remove problematic environment variables that cause the WERKZEUG_SERVER_FD error
        os.environ.pop('WERKZEUG_SERVER_FD', None)
        os.environ.pop('WERKZEUG_RUN_MAIN', None)
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,  # No debug mode with debugpy
            use_reloader=False,  # Critical: never use reloader with debugpy
            allow_unsafe_werkzeug=True,  # Required for development with debugpy
            log_output=True
        )
    else:
        # Normal production/non-debug mode
        print("🚀 Normal mode - using standard SocketIO configuration")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=flask_env == 'development',
            use_reloader=flask_env == 'development'
        )