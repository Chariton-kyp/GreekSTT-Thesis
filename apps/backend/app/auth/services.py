"""Authentication services."""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from app.constants import AUTH_MESSAGES
from flask import current_app, session, url_for, request
from flask_mail import Message

from app.extensions import db, mail
from app.users.models import User
from app.auth.models import PasswordReset, EmailVerification
from app.auth.utils import generate_verification_token
from app.auth.jwt_utils import create_auth_response, create_user_tokens
from app.services.email_service import email_service
from app.sessions.services import session_service

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def register_user(self, data: dict) -> User:
        """Register a new user."""
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            raise ValueError(AUTH_MESSAGES['EMAIL_ALREADY_REGISTERED'])
        
        if User.query.filter_by(username=data['username']).first():
            raise ValueError(AUTH_MESSAGES['USERNAME_ALREADY_EXISTS'])
        
        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password_hash=generate_password_hash(data['password']),
            phone=data.get('phone'),
            organization=data.get('organization'),
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        # SECURITY: Only get active, non-deleted users
        user = User.query.filter_by(
            email=email,
            is_active=True,
            is_deleted=False
        ).first()
        
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            # Commit successful authentication (no last_login tracking for simplified version)
            db.session.commit()
            logger.info(f"User {email} authenticated successfully")
            return user
        
        if user:
            logger.warning(f"Authentication failed for {email}: invalid password")
        else:
            logger.warning(f"Authentication failed for {email}: user not found or inactive")
        
        return None
    
    def authenticate_and_create_session(
        self, 
        email: str, 
        password: str,
        remember_me: bool = False
    ) -> tuple[Optional[User], Optional[str]]:
        """
        Authenticate user and create simple session.
        
        Returns:
            tuple: (user, jti)
        """
        # First authenticate the user
        user = self.authenticate_user(email, password)
        if not user:
            return None, None
        
        # Get request information for session creation
        ip_address = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Set session duration based on remember_me
        from datetime import timedelta
        expires_at = datetime.utcnow() + (timedelta(days=90) if remember_me else timedelta(hours=24))
        
        # Generate unique JWT ID
        jti = str(uuid.uuid4())
        
        # Create simplified session
        session = session_service.create_session(
            user=user,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user, jti
    
    def logout_user_session(self, user_id: int, jti: str) -> bool:
        """
        Logout user by deleting their session.
        
        Args:
            user_id: The user ID
            jti: The JWT ID to delete
            
        Returns:
            bool: True if session was deleted successfully
        """
        return session_service.delete_session(jti)
    
    def send_verification_email(self, user: User) -> Dict[str, Any]:
        """Send 6-digit verification code to user email."""
        # Invalidate any existing verification codes for this user
        existing_verifications = EmailVerification.query.filter_by(
            user_id=user.id, 
            verified=False
        ).all()
        for verification in existing_verifications:
            verification.verified = True  # Mark as used to prevent reuse
        
        # Create new verification record with 6-digit code
        verification = EmailVerification(
            user_id=user.id,
            verification_type='email'
        )
        db.session.add(verification)
        db.session.commit()
        
        # Send email using enhanced email service
        result = email_service.send_verification_email(user, verification.code, 'el')
        
        return {
            'code_id': verification.id,
            'expires_in': verification.get_remaining_time(),
            'can_resend_in': 120  # 2 minutes cooldown
        }
    
    def verify_email_code(self, user_id: int, code: str) -> Dict[str, Any]:
        """Verify email with 6-digit code."""
        # Find the latest verification for this user (including expired ones)
        verification = EmailVerification.query.filter_by(
            user_id=user_id,
            verified=False
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            return {
                'success': False,
                'error': 'No verification code found. Please request a new code.',
                'error_code': 'NO_CODE'
            }
        
        # First increment attempts counter
        verification.attempts += 1
        
        # Check if maximum attempts reached
        if verification.attempts > verification.max_attempts:
            db.session.commit()
            return {
                'success': False,
                'error': 'Maximum verification attempts reached. Please request a new code.',
                'error_code': 'MAX_ATTEMPTS_REACHED',
                'remaining_time': verification.get_remaining_time(),
                'attempts_left': 0
            }
        
        # Check if the code matches first (regardless of expiration)
        if verification.code != code:
            db.session.commit()  # Save the incremented attempts
            return {
                'success': False,
                'error': AUTH_MESSAGES['INVALID_VERIFICATION_CODE'],
                'error_code': 'INVALID_CODE',
                'attempts_left': verification.max_attempts - verification.attempts,
                'remaining_time': verification.get_remaining_time()
            }
        
        # Code is correct, now check if it's expired
        if verification.expires_at <= datetime.utcnow():
            db.session.commit()  # Save the incremented attempts
            return {
                'success': False,
                'error': 'Verification code has expired. Please request a new code.',
                'error_code': 'CODE_EXPIRED',
                'remaining_time': 0,
                'attempts_left': verification.max_attempts - verification.attempts
            }
        
        # Code is correct and not expired - mark as verified
        verification.verified = True
        verification.verified_at = datetime.utcnow()
        verification.user.email_verified = True
        db.session.commit()
        
        return {
            'success': True,
            'message': AUTH_MESSAGES['EMAIL_VERIFIED_SUCCESSFULLY'],
            'user_id': user_id
        }
    
    def verify_email(self, token: str) -> bool:
        """Verify email with token (legacy method for backward compatibility)."""
        verification = EmailVerification.query.filter_by(token=token).first()
        
        if verification and verification.is_valid():
            # Mark as verified
            verification.verified = True
            verification.user.email_verified = True
            db.session.commit()
            return True
        
        return False
    
    def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email with 6-digit code."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {
                'success': False,
                'error': AUTH_MESSAGES['USER_NOT_FOUND'],
                'error_code': 'USER_NOT_FOUND'
            }
        
        if user.email_verified:
            return {
                'success': False,
                'error': AUTH_MESSAGES['EMAIL_ALREADY_VERIFIED'],
                'error_code': 'ALREADY_VERIFIED'
            }
        
        # Check if we can resend (cooldown period)
        latest_verification = EmailVerification.query.filter_by(
            user_id=user.id
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if latest_verification and not latest_verification.can_resend():
            cooldown_time = latest_verification.created_at + timedelta(minutes=2)
            remaining_seconds = int((cooldown_time - datetime.utcnow()).total_seconds())
            return {
                'success': False,
                'error': f'Please wait {remaining_seconds} seconds before requesting a new code.',
                'error_code': 'COOLDOWN_ACTIVE',
                'cooldown_remaining': remaining_seconds
            }
        
        # Send new verification code
        result = self.send_verification_email(user)
        result['success'] = True
        result['message'] = 'Verification code sent successfully!'
        return result
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset with 6-digit code."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if user exists for security
            return {
                'success': True,
                'message': 'If the email exists, a reset code has been sent.',
                'code_id': None
            }
        
        # Check cooldown period for password resets
        latest_reset = PasswordReset.query.filter_by(
            user_id=user.id
        ).order_by(PasswordReset.created_at.desc()).first()
        
        if latest_reset and not latest_reset.can_resend():
            cooldown_time = latest_reset.created_at + timedelta(minutes=2)
            remaining_seconds = int((cooldown_time - datetime.utcnow()).total_seconds())
            return {
                'success': False,
                'error': f'Please wait {remaining_seconds} seconds before requesting a new reset code.',
                'error_code': 'COOLDOWN_ACTIVE',
                'cooldown_remaining': remaining_seconds
            }
        
        # Invalidate existing reset codes
        existing_resets = PasswordReset.query.filter_by(
            user_id=user.id,
            used=False
        ).all()
        for reset in existing_resets:
            reset.used = True
        
        # Create new reset record with 6-digit code
        reset = PasswordReset(
            user_id=user.id,
            reset_type='email'
        )
        db.session.add(reset)
        db.session.commit()
        
        # Send email using enhanced email service
        result = email_service.send_password_reset_email(user, reset.code, 'el')
        
        return {
            'success': True,
            'message': 'Reset code sent successfully!',
            'code_id': reset.id,
            'expires_in': reset.get_remaining_time()
        }
    
    def create_user_auth_response(self, user: User, additional_claims: Optional[Dict[str, Any]] = None, jti: str = None, remember_me: bool = False) -> Dict[str, Any]:
        """Create a complete authentication response with tokens and user data.
        
        Args:
            user: User model instance
            additional_claims: Optional additional claims for JWT
            jti: JWT ID to include in JWT claims
            
        Returns:
            Dict containing tokens and user information
        """
        # Add JWT ID to claims if provided
        if jti and additional_claims:
            additional_claims['jti'] = jti
        elif jti:
            additional_claims = {'jti': jti}
            
        return create_auth_response(user, additional_claims, remember_me)
    
    def create_user_tokens_only(self, user: User, additional_claims: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Create access and refresh tokens for a user.
        
        Args:
            user: User model instance
            additional_claims: Optional additional claims for JWT
            
        Returns:
            Dict containing access_token and refresh_token
        """
        return create_user_tokens(user, additional_claims)
    
    def verify_reset_code(self, email: str, code: str) -> Dict[str, Any]:
        """Verify password reset code."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {
                'success': False,
                'error': AUTH_MESSAGES['USER_NOT_FOUND'],
                'error_code': 'USER_NOT_FOUND'
            }
        
        # Find the latest valid reset for this user
        reset = PasswordReset.query.filter_by(
            user_id=user.id,
            used=False
        ).order_by(PasswordReset.created_at.desc()).first()
        
        if not reset:
            return {
                'success': False,
                'error': 'No reset code found. Please request a new reset code.',
                'error_code': 'NO_CODE'
            }
        
        if not reset.is_valid():
            return {
                'success': False,
                'error': 'Reset code has expired or maximum attempts reached.',
                'error_code': 'EXPIRED_OR_MAX_ATTEMPTS',
                'remaining_time': reset.get_remaining_time(),
                'attempts_left': reset.max_attempts - reset.attempts
            }
        
        # Verify the code
        if reset.verify_code(code):
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Reset code verified successfully!',
                'reset_token': reset.id,  # Use reset ID as temp token for password change
                'user_id': user.id
            }
        else:
            db.session.commit()  # Save the incremented attempts
            
            return {
                'success': False,
                'error': AUTH_MESSAGES['INVALID_RESET_CODE'],
                'error_code': 'INVALID_CODE',
                'attempts_left': reset.max_attempts - reset.attempts,
                'remaining_time': reset.get_remaining_time()
            }
    
    def reset_password_with_token(self, reset_token: int, new_password: str) -> Dict[str, Any]:
        """Reset password after code verification using token."""
        reset = PasswordReset.query.filter_by(id=reset_token, used=True).first()
        
        if not reset:
            return {
                'success': False,
                'error': 'Invalid or expired reset session.',
                'error_code': 'INVALID_SESSION'
            }
        
        # Check if reset was used recently (within 5 minutes for security)
        if reset.used_at and (datetime.utcnow() - reset.used_at).total_seconds() > 300:
            return {
                'success': False,
                'error': 'Reset session has expired. Please start over.',
                'error_code': 'SESSION_EXPIRED'
            }
        
        # Update password
        reset.user.password_hash = generate_password_hash(new_password)
        
        # Invalidate all other reset codes for this user
        other_resets = PasswordReset.query.filter(
            PasswordReset.user_id == reset.user_id,
            PasswordReset.id != reset.id,
            PasswordReset.used == False
        ).all()
        for other_reset in other_resets:
            other_reset.used = True
        
        db.session.commit()
        
        return {
            'success': True,
            'message': AUTH_MESSAGES['PASSWORD_RESET_SUCCESSFUL'],
            'user_id': reset.user_id
        }
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token (legacy method for backward compatibility)."""
        reset = PasswordReset.query.filter_by(token=token).first()
        
        if reset and reset.is_valid():
            # Update password
            reset.user.password_hash = generate_password_hash(new_password)
            reset.used = True
            db.session.commit()
            return True
        
        return False
    
    def verify_password_reset_code(self, email: str, code: str) -> Dict[str, Any]:
        """Verify a 6-digit password reset code."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {
                'success': False,
                'error': AUTH_MESSAGES['USER_NOT_FOUND'],
                'error_code': 'USER_NOT_FOUND'
            }
        
        # Find the latest valid reset for this user
        reset = PasswordReset.query.filter_by(
            user_id=user.id,
            used=False
        ).order_by(PasswordReset.created_at.desc()).first()
        
        if not reset:
            return {
                'success': False,
                'error': 'No reset code found. Please request a new reset code.',
                'error_code': 'NO_CODE'
            }
        
        if not reset.is_valid():
            return {
                'success': False,
                'error': 'Reset code has expired or maximum attempts reached.',
                'error_code': 'EXPIRED_OR_MAX_ATTEMPTS',
                'remaining_time': reset.get_remaining_time(),
                'attempts_left': reset.max_attempts - reset.attempts
            }
        
        # Verify the code
        if reset.verify_code(code):
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Reset code verified successfully!',
                'reset_token': reset.id,  # Use reset ID as temp token for password change
                'user_id': user.id
            }
        else:
            db.session.commit()  # Save the incremented attempts
            
            return {
                'success': False,
                'error': AUTH_MESSAGES['INVALID_RESET_CODE'],
                'error_code': 'INVALID_CODE',
                'attempts_left': reset.max_attempts - reset.attempts,
                'remaining_time': reset.get_remaining_time()
            }
    
    def reset_password_with_code(self, email: str, code: str, new_password: str) -> Dict[str, Any]:
        """Reset password using verified code."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {
                'success': False,
                'error': AUTH_MESSAGES['USER_NOT_FOUND'],
                'error_code': 'USER_NOT_FOUND'
            }
        
        # Find the latest valid reset for this user
        reset = PasswordReset.query.filter_by(
            user_id=user.id,
            used=False
        ).order_by(PasswordReset.created_at.desc()).first()
        
        if not reset:
            return {
                'success': False,
                'error': 'No reset code found. Please request a new reset code.',
                'error_code': 'NO_CODE'
            }
        
        if not reset.is_valid():
            return {
                'success': False,
                'error': 'Reset code has expired or maximum attempts reached.',
                'error_code': 'EXPIRED_OR_MAX_ATTEMPTS',
                'remaining_time': reset.get_remaining_time(),
                'attempts_left': reset.max_attempts - reset.attempts
            }
        
        # Verify the code and reset password
        if reset.verify_code(code):
            # Update password
            user.password_hash = generate_password_hash(new_password)
            
            # Invalidate all other reset codes for this user
            other_resets = PasswordReset.query.filter(
                PasswordReset.user_id == user.id,
                PasswordReset.id != reset.id,
                PasswordReset.used == False
            ).all()
            for other_reset in other_resets:
                other_reset.used = True
            
            db.session.commit()
            
            return {
                'success': True,
                'message': AUTH_MESSAGES['PASSWORD_RESET_SUCCESSFUL'],
                'user_id': user.id
            }
        else:
            db.session.commit()  # Save the incremented attempts
            
            return {
                'success': False,
                'error': AUTH_MESSAGES['INVALID_RESET_CODE'],
                'error_code': 'INVALID_CODE',
                'attempts_left': reset.max_attempts - reset.attempts,
                'remaining_time': reset.get_remaining_time()
            }
    
    def verify_email_with_code(self, user_id: int, code: str) -> Dict[str, Any]:
        """Verify email using 6-digit code."""
        # Find the latest verification for this user (including expired ones)
        verification = EmailVerification.query.filter_by(
            user_id=user_id,
            verified=False
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            return {
                'success': False,
                'error': 'No verification code found. Please request a new code.',
                'error_code': 'NO_CODE'
            }
        
        # First increment attempts counter
        verification.attempts += 1
        
        # Check if maximum attempts reached
        if verification.attempts > verification.max_attempts:
            db.session.commit()
            return {
                'success': False,
                'error': 'Maximum verification attempts reached. Please request a new code.',
                'error_code': 'MAX_ATTEMPTS_REACHED',
                'remaining_time': verification.get_remaining_time(),
                'attempts_left': 0
            }
        
        # Check if the code matches first (regardless of expiration)
        if verification.code != code:
            db.session.commit()  # Save the incremented attempts
            return {
                'success': False,
                'error': AUTH_MESSAGES['INVALID_VERIFICATION_CODE'],
                'error_code': 'INVALID_CODE',
                'attempts_left': verification.max_attempts - verification.attempts,
                'remaining_time': verification.get_remaining_time()
            }
        
        # Code is correct, now check if it's expired
        if verification.expires_at <= datetime.utcnow():
            db.session.commit()  # Save the incremented attempts
            return {
                'success': False,
                'error': 'Verification code has expired. Please request a new code.',
                'error_code': 'CODE_EXPIRED',
                'remaining_time': 0,
                'attempts_left': verification.max_attempts - verification.attempts
            }
        
        # Code is correct and not expired - mark as verified
        verification.verified = True
        verification.verified_at = datetime.utcnow()
        verification.user.email_verified = True
        db.session.commit()
        
        return {
            'success': True,
            'message': AUTH_MESSAGES['EMAIL_VERIFIED_SUCCESSFULLY'],
            'user_id': user_id
        }
    
    def resend_verification_code(self, user_id: int) -> Dict[str, Any]:
        """Resend email verification code."""
        user = User.query.get(user_id)
        
        if not user:
            return {
                'success': False,
                'error': AUTH_MESSAGES['USER_NOT_FOUND'],
                'error_code': 'USER_NOT_FOUND'
            }
        
        if user.email_verified:
            return {
                'success': False,
                'error': AUTH_MESSAGES['EMAIL_ALREADY_VERIFIED'],
                'error_code': 'ALREADY_VERIFIED'
            }
        
        # Check if we can resend (cooldown period)
        latest_verification = EmailVerification.query.filter_by(
            user_id=user.id
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if latest_verification and not latest_verification.can_resend():
            cooldown_time = latest_verification.created_at + timedelta(minutes=2)
            remaining_seconds = int((cooldown_time - datetime.utcnow()).total_seconds())
            return {
                'success': False,
                'error': f'Please wait {remaining_seconds} seconds before requesting a new code.',
                'error_code': 'COOLDOWN_ACTIVE',
                'cooldown_remaining': remaining_seconds
            }
        
        # Send new verification code
        result = self.send_verification_email(user)
        result['success'] = True
        result['message'] = 'Verification code sent successfully!'
        return result


# Service instances
auth_service = AuthService()