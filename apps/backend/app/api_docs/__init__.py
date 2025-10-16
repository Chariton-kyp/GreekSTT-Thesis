"""API documentation namespaces."""

from flask_restx import Namespace

# Create namespaces for different API sections
auth_ns = Namespace('auth', description='Authentication operations')
users_ns = Namespace('users', description='User management operations')
audio_ns = Namespace('audio', description='Audio file operations')
transcription_ns = Namespace('transcriptions', description='Transcription operations')
templates_ns = Namespace('templates', description='Template management operations')
research_ns = Namespace('research', description='Research analytics and usage operations')
health_ns = Namespace('health', description='Health check operations')

# IMPORTANT: Resource classes are commented out to prevent Flask-RESTX from creating
# conflicting endpoints with the Blueprint routes. Flask-RESTX is used ONLY for Swagger
# documentation models, NOT for actual endpoint implementation.
#
# from .health import *
# from .auth import *
# from .users import *
# from .audio import *
# from .transcriptions import *