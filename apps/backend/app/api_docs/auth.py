"""Authentication API documentation."""

from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required

from app.api_docs import auth_ns
from app.api_docs.models import (
    login_model, register_model, user_response_model, error_model
)


@auth_ns.route('/login')
class AuthLoginAPI(Resource):
    """User authentication."""
    
    @auth_ns.doc('login')
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.marshal_with(user_response_model, code=200)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    def post(self):
        """
        Authenticate user with email and password.
        
        Returns JWT access token and refresh token upon successful login.
        Supports Greek language interface and academic user verification.
        """
        pass  # Documentation only - implementation handled by Blueprint route


@auth_ns.route('/register')
class AuthRegisterAPI(Resource):
    """User registration."""
    
    @auth_ns.doc('register')
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.marshal_with(user_response_model, code=201)
    @auth_ns.response(400, 'Invalid registration data', error_model)
    @auth_ns.response(409, 'User already exists', error_model)
    def post(self):
        """
        Register new user account.
        
        Creates new user account with email verification requirement.
        Supports academic sectors and Greek language preferences.
        """
        pass  # Documentation only - implementation handled by Blueprint route


@auth_ns.route('/verify-email')
class AuthVerifyEmailAPI(Resource):
    """Email verification."""
    
    @auth_ns.doc('verify_email')
    @auth_ns.expect(auth_ns.model('EmailVerification', {
        'email': fields.String(required=True, description='User email'),
        'verification_code': fields.String(required=True, description='6-digit verification code')
    }), validate=True)
    @auth_ns.response(200, 'Email verified successfully')
    @auth_ns.response(400, 'Invalid verification code', error_model)
    def post(self):
        """
        Verify user email with 6-digit code.
        
        Completes user registration process by verifying email address.
        """
        pass  # Documentation only


@auth_ns.route('/logout')
class AuthLogoutAPI(Resource):
    """User logout."""
    
    @auth_ns.doc('logout', security='Bearer')
    @auth_ns.response(200, 'Logout successful')
    @auth_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def post(self):
        """
        Logout user and invalidate tokens.
        
        Adds current JWT token to blacklist to prevent further use.
        """
        pass  # Documentation only


@auth_ns.route('/me')
class AuthMeAPI(Resource):
    """Current user information."""
    
    @auth_ns.doc('get_current_user', security='Bearer')
    @auth_ns.marshal_with(user_response_model, code=200)
    @auth_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get current authenticated user information.
        
        Returns detailed user profile including verification status.
        """
        pass  # Documentation only