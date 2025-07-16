"""Authentication routes."""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from app.auth.jwt_utils import refresh_user_token, create_user_tokens
from app.common.decorators import validate_request
from app.schemas.auth import (
    LoginSchema, RegisterSchema, 
    ResetPasswordRequestSchema, ResetPasswordSchema,
    EmailVerificationCodeSchema, PasswordResetCodeVerificationSchema,
    ResetPasswordWithCodeSchema
)
from app.auth.services import AuthService
from app.models import BlacklistToken
from app.extensions import db
from app.common.responses import (
    verification_error_response, auth_success_response, auth_error_response,
    error_response, success_response
)
from app.constants.multilingual_messages import get_auth_message
from app.utils.logging_middleware import log_business_operation
from app.utils.correlation_logger import get_correlation_logger
from app.auth.models import PasswordReset
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

logger = get_correlation_logger(__name__)

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
@validate_request(RegisterSchema)
@log_business_operation('user_registration', {'method': 'email_password'})
def register(validated_data):
    """Register a new user."""
    try:
        email = validated_data['email']
        username = validated_data['username']
        
        logger.info(f"User registration started: {email}")
        
        user = auth_service.register_user(validated_data)
        
        logger.info(f"User registration successful: {user.id}")
        
        # Send verification email if enabled
        if current_app.config.get('ENABLE_EMAIL_VERIFICATION'):
            logger.info(f"Sending verification email to {email}")
            auth_service.send_verification_email(user)
            message = get_auth_message('REGISTRATION_SUCCESSFUL')
            
            logger.info(f"Creating limited session for unverified user {user.id}")
            
            # Create limited-access session for unverified user (hybrid approach)
            additional_claims = {
                'login_method': 'registration',
                'registration_time': user.created_at.isoformat() if user.created_at else None,
                'verification_required': True
            }
            
            user, jti = auth_service.authenticate_and_create_session(
                validated_data['email'],
                validated_data['password']
            )
            
            logger.info(
                f"✅ REGISTRATION COMPLETE WITH VERIFICATION | "
                f"user_id={user.id} | "
                f"jti={jti[:8]}... | "
                f"verification_required=true"
            )
            
            auth_response = auth_service.create_user_auth_response(user, additional_claims, jti)
            auth_response['message'] = message
            auth_response['message_type'] = 'success'
            auth_response['requires_verification'] = True
            
            return jsonify(auth_response), 201
        else:
            logger.info(f"🔑 AUTO-LOGIN AFTER REGISTRATION | user_id={user.id} | verification_disabled=true")
            
            # If email verification is disabled, automatically log the user in
            additional_claims = {
                'login_method': 'registration',
                'registration_time': user.created_at.isoformat() if user.created_at else None
            }
            
            # Create session for the new user
            user, jti = auth_service.authenticate_and_create_session(
                validated_data['email'],
                validated_data['password']
            )
            
            logger.info(
                f"✅ REGISTRATION COMPLETE WITH AUTO-LOGIN | "
                f"user_id={user.id} | "
                f"jti={jti[:8]}... | "
                f"verification_required=false"
            )
            
            auth_response = auth_service.create_user_auth_response(user, additional_claims, jti)
            auth_response['message'] = get_auth_message('REGISTRATION_SUCCESSFUL_NO_VERIFICATION')
            auth_response['message_type'] = 'success'
            auth_response['requires_verification'] = False
            
            return jsonify(auth_response), 201
        
    except ValueError as e:
        logger.error(
            f"❌ REGISTRATION FAILED - VALIDATION ERROR | "
            f"email={validated_data.get('email')} | "
            f"error={str(e)} | "
            f"client_ip={request.remote_addr}"
        )
        
        return error_response(
            message=str(e),
            error_code='VALIDATION_ERROR',
            status_code=400
        )
    except Exception as e:
        logger.error(
            f"💥 REGISTRATION FAILED - SYSTEM ERROR | "
            f"email={validated_data.get('email')} | "
            f"error={str(e)} | "
            f"client_ip={request.remote_addr}"
        )

        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/login', methods=['POST'])
@validate_request(LoginSchema)
@log_business_operation('user_login', {'method': 'email_password'})
def login(validated_data):
    """Login a user."""
    try:
        email = validated_data['email']
        remember_me = validated_data.get('remember_me', False)
        
        logger.info(
            f"🔐 USER LOGIN ATTEMPT | "
            f"email={email} | "
            f"remember_me={remember_me} | "
            f"client_ip={request.remote_addr} | "
            f"user_agent={request.headers.get('User-Agent', 'unknown')[:50]}..."
        )
        
        from app.users.models import User
        
        # First, find user by email to check for lockout
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user:
            logger.info(f"👤 USER FOUND | user_id={user.id} | email={email} | academic_user=true")
        else:
            logger.warning(f"⚠️ USER NOT FOUND | email={email} | client_ip={request.remote_addr}")
        
        # Attempt to authenticate user and create session
        logger.info(f"🔍 AUTHENTICATING USER | email={email} | attempting_authentication=true")
        
        authenticated_user, jti = auth_service.authenticate_and_create_session(
            email,
            validated_data['password'],
            remember_me=remember_me
        )
        
        if not authenticated_user:
            logger.warning(f"❌ AUTHENTICATION FAILED | email={email} | invalid_credentials=true | client_ip={request.remote_addr}")
            
            return auth_error_response(
                message_key='INVALID_CREDENTIALS',
                error_code='INVALID_CREDENTIALS',
                status_code=401
            )
        
        logger.info(
            f"✅ AUTHENTICATION SUCCESS | "
            f"user_id={authenticated_user.id} | "
            f"email={email} | "
            f"username={authenticated_user.username} | "
            f"type=student | "
            f"email_verified={authenticated_user.email_verified} | "
            f"jti={jti[:8]}... | "
            f"remember_me={remember_me}"
        )
        
        # Create authentication response with custom JWT claims
        additional_claims = {
            'login_method': 'password',
            'login_time': datetime.utcnow().isoformat(),  # Use current time for simplified thesis version
            'remember_me': remember_me
        }
        
        auth_response = auth_service.create_user_auth_response(
            authenticated_user, 
            additional_claims, 
            jti, 
            remember_me=remember_me
        )
        auth_response['message'] = get_auth_message('LOGIN_SUCCESSFUL')
        auth_response['message_type'] = 'success'
        
        logger.info(
            f"🎯 LOGIN COMPLETE | "
            f"user_id={authenticated_user.id} | "
            f"session_created=true | "
            f"jwt_issued=true | "
            f"response_status=200"
        )
        
        return jsonify(auth_response), 200
        
    except Exception as e:
        # Log system error during login with detailed traceback
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"🚨 LOGIN SYSTEM ERROR: {str(e)}")
        logger.error(f"🚨 FULL TRACEBACK:\n{error_details}")

        current_app.logger.error(f"Login error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@log_business_operation('user_logout')
def logout():
    """Logout a user by blacklisting their token."""
    try:
        user_id = get_jwt_identity()
        jti = get_jwt()['jti']
        jwt_claims = get_jwt()
        session_id = jwt_claims.get('session_id')
        
        logger.info(
            f"🚪 USER LOGOUT STARTED | "
            f"user_id={user_id} | "
            f"session_id={session_id[:8] + '...' if session_id else 'none'} | "
            f"jti={jti[:8]}... | "
            f"client_ip={request.remote_addr}"
        )
        
        # Add token to blacklist
        blacklist_token = BlacklistToken(jti=jti)
        db.session.add(blacklist_token)
        db.session.commit()
        
        logger.info(f"🔒 JWT TOKEN BLACKLISTED | user_id={user_id} | jti={jti[:8]}...")
        
        # Terminate session if present
        session_terminated = False
        if session_id:
            session_terminated = auth_service.logout_user_session(user_id, session_id)
            logger.info(f"📱 SESSION TERMINATED | user_id={user_id} | session_id={session_id[:8]}... | terminated={session_terminated}")
        else:
            logger.info(f"⚠️ NO SESSION TO TERMINATE | user_id={user_id}")
        
        logger.info(
            f"✅ LOGOUT COMPLETE | "
            f"user_id={user_id} | "
            f"token_blacklisted=true | "
            f"session_terminated={session_terminated} | "
            f"status=success"
        )
        
        return auth_success_response(
            message_key='LOGOUT_SUCCESSFUL',
            data={'session_terminated': session_terminated}
        )
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh an access token with updated custom claims."""
    try:
        user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        
        logger.info(
            f"🔄 TOKEN REFRESH STARTED | "
            f"user_id={user_id} | "
            f"refresh_jti={jwt_claims.get('jti', 'unknown')[:8]}... | "
            f"client_ip={request.remote_addr}"
        )
        
        # Get user from database
        from app.users.models import User
        user = User.query.filter_by(id=user_id, is_active=True, is_deleted=False).first()
        if not user:
            raise ValueError("User not found or inactive")
        
        # Create new tokens with fresh user data and custom claims
        from app.auth.jwt_utils import create_user_tokens
        tokens = create_user_tokens(user)
        
        logger.info(f"✅ TOKEN REFRESH SUCCESS | user_id={user_id} | new_tokens_issued=true")
        
        response_data = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data=response_data
        )
        
    except ValueError as e:
        current_app.logger.error(f"Token refresh error - user issue: {str(e)}")
        return auth_error_response(
            message_key='USER_NOT_FOUND',
            error_code='USER_NOT_FOUND',
            status_code=401
        )
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/verify-email-code', methods=['POST'])
@jwt_required()
@validate_request(EmailVerificationCodeSchema)
def verify_email_code(validated_data):
    """Verify user email with 6-digit code."""
    try:
        user_id = get_jwt_identity()
        code = validated_data['code']
        
        logger.info(
            f"📧 EMAIL VERIFICATION STARTED | "
            f"user_id={user_id} | "
            f"code={code[:2]}**** | "
            f"client_ip={request.remote_addr}"
        )
        
        # Check if email verification is enabled
        if not current_app.config.get('ENABLE_EMAIL_VERIFICATION', True):
            logger.warning(f"⚠️ EMAIL VERIFICATION DISABLED | user_id={user_id} | environment=development")
            return auth_error_response(
                message='Email verification is disabled in this environment',
                error_code='VERIFICATION_DISABLED',
                status_code=400
            )
        
        result = auth_service.verify_email_code(user_id, code)
        
        if result['success']:
            logger.info(
                f"✅ EMAIL VERIFICATION SUCCESS | "
                f"user_id={user_id} | "
                f"code={code[:2]}**** | "
                f"method=6_digit_code"
            )
            
            # Get updated user data and issue new tokens with fresh claims
            from app.users.services import UserService
            user_service = UserService()
            user = user_service.get_user_by_id(user_id)
            
            if user:
                # Create fresh tokens with updated email_verified status
                tokens = create_user_tokens(user)
                
                # Send welcome email after successful verification
                try:
                    from app.services.email_service import email_service
                    email_service.send_welcome_email(user, language='el')
                    logger.info(f"📧 WELCOME EMAIL SENT | user_id={user_id}")
                except Exception as email_error:
                    # Don't fail the verification if email fails
                    logger.warning(f"⚠️ Failed to send welcome email | user_id={user_id} | error={str(email_error)}")
                
                return auth_success_response(
                    message_key='EMAIL_VERIFIED_SUCCESSFULLY',
                    data={
                        'access_token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                        'email_verified': True
                    }
                )
            else:
                return auth_success_response(
                    message_key='EMAIL_VERIFIED_SUCCESSFULLY'
                )
        else:
            logger.warning(
                f"❌ EMAIL VERIFICATION FAILED | "
                f"user_id={user_id} | "
                f"code={code[:2]}**** | "
                f"error={result.get('error', 'unknown')} | "
                f"attempts_left={result.get('attempts_left', 0)}"
            )
            
            return verification_error_response(
                error_code=result.get('error_code', 'INVALID_CODE'),
                attempts_left=result.get('attempts_left'),
                remaining_time=result.get('remaining_time')
            )
            
    except Exception as e:
        logger.error(f"Email verification error", {'error': str(e)})
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify user email with token (legacy endpoint)."""
    try:
        if auth_service.verify_email(token):
            return auth_success_response(
                message_key='EMAIL_VERIFIED_SUCCESSFULLY'
            )
        else:
            return auth_error_response(
                message='Invalid or expired token',
                error_code='INVALID_TOKEN',
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Email verification error", {'error': str(e)})
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/resend-verification', methods=['POST'])
@jwt_required()
def resend_verification():
    """Resend verification email with 6-digit code."""
    try:
        user_id = get_jwt_identity()
        
        # Get user email for resending
        from app.users.models import User
        user = User.query.get(user_id)
        if not user:
            return auth_error_response(
                message_key='USER_NOT_FOUND',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        email = user.email
        
        from app.users.models import User
        user = User.query.filter_by(email=email).first()
        
        result = auth_service.resend_verification_email(email)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 400
            if result.get('error_code') == 'COOLDOWN_ACTIVE':
                status_code = 429  # Too Many Requests
            elif result.get('error_code') == 'ALREADY_VERIFIED':
                status_code = 409  # Conflict
            
            return jsonify(result), status_code
            
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/forgot-password', methods=['POST'])
@validate_request(ResetPasswordRequestSchema)
def forgot_password(validated_data):
    """Request a password reset for non-authenticated users."""
    try:
        from app.users.models import User
        user = User.query.filter_by(email=validated_data['email']).first()
        
        logger.info(
            f"🔐 FORGOT PASSWORD REQUEST | "
            f"email={validated_data['email']} | "
            f"user_exists={user is not None} | "
            f"client_ip={request.remote_addr}"
        )
        
        result = auth_service.request_password_reset(validated_data['email'])
        
        if result['success']:
            return auth_success_response(
                message_key='PASSWORD_RESET_SENT',
                data={
                    'code_id': result.get('code_id'),
                    'expires_in': result.get('expires_in')
                }
            )
        else:
            status_code = 400
            if result.get('error_code') == 'COOLDOWN_ACTIVE':
                status_code = 429  # Too Many Requests
            
            return auth_error_response(
                message_key='USER_NOT_FOUND' if result.get('error_code') == 'USER_NOT_FOUND' else 'BAD_REQUEST',
                error_code=result.get('error_code', 'REQUEST_FAILED'),
                status_code=status_code
            )
            
    except Exception as e:
        current_app.logger.error(f"Password reset request error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/request-password-reset', methods=['POST'])
@jwt_required()
def request_password_reset_authenticated():
    """Request password reset for authenticated users (more restrictive)."""
    try:
        user_id = get_jwt_identity()
        from app.users.models import User
        user = User.query.get(user_id)
        
        if not user:
            return auth_error_response(
                message_key='USER_NOT_FOUND',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        logger.info(
            f"🔐 AUTHENTICATED PASSWORD RESET REQUEST | "
            f"user_id={user_id} | "
            f"email={user.email} | "
            f"client_ip={request.remote_addr}"
        )
        
        result = auth_service.request_password_reset(user.email)
        
        if result['success']:
            return auth_success_response(
                message_key='PASSWORD_RESET_SENT',
                data={
                    'code_id': result.get('code_id'),
                    'expires_in': result.get('expires_in'),
                    'email': user.email  # Include email since they're authenticated
                }
            )
        else:
            status_code = 400
            if result.get('error_code') == 'COOLDOWN_ACTIVE':
                status_code = 429  # Too Many Requests
            
            return auth_error_response(
                message_key='BAD_REQUEST',
                error_code=result.get('error_code', 'REQUEST_FAILED'),
                status_code=status_code
            )
            
    except Exception as e:
        current_app.logger.error(f"Authenticated password reset request error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/verify-reset-code', methods=['POST'])
@validate_request(PasswordResetCodeVerificationSchema)
def verify_reset_code(validated_data):
    """Verify password reset code."""
    try:
        email = validated_data['email']
        code = validated_data['code']

        result = auth_service.verify_reset_code(email, code)
        
        if result['success']:
            return auth_success_response(
                message_key='RESET_CODE_VERIFIED',
                data={
                    'reset_token': result.get('reset_token'),
                    'next_step': 'enter_new_password'
                }
            )
        else:
            status_code = 400
            if result.get('error_code') == 'EXPIRED_OR_MAX_ATTEMPTS':
                status_code = 410  # Gone
            elif result.get('error_code') == 'NO_CODE':
                status_code = 404  # Not Found
            
            return verification_error_response(
                error_code=result.get('error_code', 'INVALID_CODE'),
                attempts_left=result.get('attempts_left'),
                remaining_time=result.get('remaining_time'),
                status_code=status_code
            )
            
    except Exception as e:
        current_app.logger.error(f"Reset code verification error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/reset-password-with-code', methods=['POST'])
@validate_request(ResetPasswordWithCodeSchema)
def reset_password_with_code(validated_data):
    """Reset password after code verification."""
    try:
        email = validated_data['email']
        code = validated_data['code']
        new_password = validated_data['password']
        
        from app.users.models import User
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return auth_error_response(
                message_key='USER_NOT_FOUND',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        # Find the most recent used reset code for this user
        reset = PasswordReset.query.filter_by(
            user_id=user.id, 
            code=code,
            used=True
        ).order_by(PasswordReset.used_at.desc()).first()
        
        if not reset:
            return auth_error_response(
                message_key='NO_CODE',
                error_code='NO_CODE',
                status_code=404
            )
        
        # Check if reset was used recently (within 10 minutes for flexibility)
        if reset.used_at and (datetime.utcnow() - reset.used_at).total_seconds() > 600:
            return auth_error_response(
                message_key='RESET_CODE_EXPIRED',
                error_code='SESSION_EXPIRED',
                status_code=410
            )
        
        # Update password directly (reset is already verified)
        reset.user.password_hash = generate_password_hash(new_password)
        
        # Mark all other reset codes for this user as invalid
        other_resets = PasswordReset.query.filter(
            PasswordReset.user_id == reset.user_id,
            PasswordReset.id != reset.id
        ).all()
        
        for other_reset in other_resets:
            other_reset.used = True
            other_reset.used_at = datetime.utcnow()
        
        # Mark this reset as fully completed
        reset.used_at = datetime.utcnow()
        
        db.session.commit()
        
        result = {
            'success': True,
            'user_id': reset.user_id,
            'message': 'Password reset successful'
        }
        
        # Send password changed notification email
        try:
            from app.services.email_service import email_service
            email_service.send_password_changed_email(
                user=reset.user,
                change_type='reset',
                client_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'unknown'),
                language='el'
            )
            logger.info(f"📧 PASSWORD CHANGED EMAIL SENT | user_id={reset.user.id}")
        except Exception as email_error:
            # Don't fail the password reset if email fails
            logger.warning(f"⚠️ Failed to send password changed email | user_id={reset.user.id} | error={str(email_error)}")
        
        # Create new session for auto-login after password reset
        try:
            from app.sessions.services import session_service
            
            # Extract request information for session creation
            ip_address = request.remote_addr or '127.0.0.1'
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # Generate unique JWT ID
            jti = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create new session for the user
            session = session_service.create_session(
                user=reset.user,
                jti=jti,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"🔐 AUTO-LOGIN SESSION CREATED | user_id={reset.user.id} | jti={jti[:8]}...")
            
            # Create auth response with JWT ID
            additional_claims = {
                'login_method': 'password_reset',
                'reset_time': datetime.utcnow().isoformat()
            }
            
            auth_response = auth_service.create_user_auth_response(
                reset.user,
                additional_claims,
                jti,
                remember_me=False
            )
            
            # Return success with tokens and redirect info
            return auth_success_response(
                message_key='PASSWORD_RESET_SUCCESSFUL',
                data={
                    'access_token': auth_response['access_token'],
                    'refresh_token': auth_response['refresh_token'],
                    'user': auth_response['user'],
                    'redirect_to': '/app/dashboard',
                }
            )
            
        except Exception as token_error:
            logger.warning(f"⚠️ Failed to create auto-login session | error={str(token_error)}")
            import traceback
            logger.debug(f"Auto-login error traceback: {traceback.format_exc()}")
            
            # Fallback to basic success without auto-login
            return auth_success_response(
                message_key='PASSWORD_RESET_SUCCESSFUL',
                data={'redirect_to': '/login'}
            )
            
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@auth_bp.route('/reset-password', methods=['POST'])
@validate_request(ResetPasswordSchema)
def reset_password(validated_data):
    """Reset password with token (legacy endpoint)."""
    try:
        if auth_service.reset_password(
            validated_data['token'],
            validated_data['password']
        ):
            return auth_success_response(
                message_key='PASSWORD_RESET_SUCCESSFUL'
            )
        else:
            return auth_error_response(
                message='Invalid or expired token',
                error_code='INVALID_TOKEN',
                status_code=400
            )
            
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )