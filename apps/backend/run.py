import os
import sys

print("🔧 Using threading mode for WebSocket")

from app import create_app

flask_env = os.environ.get('FLASK_ENV', 'development')
app, socketio = create_app(flask_env)

if __name__ == "__main__":
    print("🔧 Backend running on HTTP only")
    
    running_under_debugpy = os.environ.get('RUNNING_UNDER_DEBUGPY', 'false').lower() == 'true'
    
    print(f"🚀 Starting Flask backend with SocketIO support")
    print(f"🔧 Environment: {flask_env}")
    print(f"🐞 Running under debugpy: {running_under_debugpy}")
    print(f"🌐 WebSocket support: Enabled")
    
    if running_under_debugpy:
        print("🔧 Debugpy detected - using debugpy-compatible SocketIO configuration")
        
        os.environ.pop('WERKZEUG_SERVER_FD', None)
        os.environ.pop('WERKZEUG_RUN_MAIN', None)
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
            log_output=True
        )
    else:
        print("🚀 Normal mode - using standard SocketIO configuration")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=flask_env == 'development',
            use_reloader=flask_env == 'development'
        )