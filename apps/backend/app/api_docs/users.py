"""User management API documentation."""

from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required

from app.api_docs import users_ns
from app.api_docs.models import (
    user_response_model, error_model
)


@users_ns.route('/profile')
class UserProfileAPI(Resource):
    """User profile management."""
    
    @users_ns.doc('get_user_profile', security='Bearer')
    @users_ns.marshal_with(user_response_model, code=200)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get user profile information.
        
        Returns current user's profile including academic details.
        """
        pass  # Documentation only
    
    @users_ns.doc('update_user_profile', security='Bearer')
    @users_ns.expect(users_ns.model('UserUpdate', {
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'sector': fields.String(description='Professional sector', 
                               enum=['academic', 'legal', 'business', 'general'])
    }), validate=True)
    @users_ns.marshal_with(user_response_model, code=200)
    @users_ns.response(400, 'Invalid request data', error_model)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def put(self):
        """
        Update user profile.
        
        Updates user's personal information and preferences.
        """
        pass  # Documentation only


@users_ns.route('/statistics')
class UserStatisticsAPI(Resource):
    """User usage statistics."""
    
    @users_ns.doc('get_user_statistics', security='Bearer')
    @users_ns.marshal_with(users_ns.model('UserStatistics', {
        'total_transcriptions': fields.Integer(description='Total transcriptions'),
        'total_audio_hours': fields.Float(description='Total audio processed'),
        'preferred_model': fields.String(description='Most used ASR model'),
        'average_accuracy': fields.Float(description='Average transcription accuracy')
    }), code=200)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get user usage statistics.
        
        Returns comprehensive usage analytics for research purposes.
        """
        pass  # Documentation only