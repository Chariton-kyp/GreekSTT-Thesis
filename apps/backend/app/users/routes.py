"""User routes."""

import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.common.decorators import validate_request
from app.schemas.users import UpdateUserSchema, ChangePasswordSchema
from app.users.services import UserService
from app.auth.verification_required import verification_optional, verification_required
from app.utils.logging_middleware import log_business_operation
from app.utils.correlation_logger import get_correlation_logger, log_data_access
from app.common.responses import (
    user_success_response, user_error_response, error_response, success_response
)

logger = get_correlation_logger(__name__)

users_bp = Blueprint('users', __name__)
user_service = UserService()


@users_bp.route('/me', methods=['GET'])
@jwt_required()
@verification_optional
@log_business_operation('get_current_user_profile')
def get_current_user():
    """Get current user profile with SECURE validation."""
    try:
        user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        
        # Log user journey step
        logger.user_journey("profile_access_start", {"user_id": user_id})
        log_data_access("user_profile", user_id, "read")
        
        logger.info(f"Retrieving profile for user {user_id}")
        
        # SECURITY: Get user from database
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"User not found in database")
            return user_error_response(
                message_key='USER_NOT_FOUND',
                message_category='AUTH_MESSAGES',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        # SECURITY: Validate user is still active and not banned
        if not user.is_active:
            logger.warning(f"User is inactive")
            return user_error_response(
                message_key='ACCOUNT_DISABLED',
                message_category='AUTH_MESSAGES',
                error_code='ACCOUNT_DISABLED',
                status_code=403
            )
        
        # SECURITY: Validate JWT claims match current user state
        if jwt_claims.get('email') != user.email:
            logger.warning(f"JWT email mismatch detected")
            return user_error_response(
                message_key='SESSION_EXPIRED',
                message_category='AUTH_MESSAGES',
                error_code='TOKEN_INVALID',
                status_code=401
            )
        
        # Return secure user data with backend masking for display
        user_data = user.to_dict()
        
        # Security: Remove sensitive database fields
        user_data.pop('id', None)  # Never expose DB IDs
        
        # Backend masking for security - don't send full sensitive data over network
        if user_data.get('email'):
            email_parts = user_data['email'].split('@')
            if len(email_parts) == 2:
                user_data['email_display'] = f"{email_parts[0][:3]}***@{email_parts[1]}"
            else:
                user_data['email_display'] = user_data['email']
            # Keep full email only for settings/editing endpoints, not here
            user_data.pop('email', None)
        
        if user_data.get('phone'):
            phone = user_data['phone']
            user_data['phone_display'] = f"***{phone[-4:]}" if len(phone) > 4 else "***"
            # Keep full phone only for settings/editing endpoints, not here  
            user_data.pop('phone', None)
        else:
            user_data['phone_display'] = None
        
        # Ensure empty strings instead of null for frontend
        user_data['organization'] = user.organization or ''
        
        # Add user data - academic version
        user_data.update({
            'user_type': 'student',
            'email_verified': user.primary_email_verified
        })
        
        response_data = user_data
        
        # Log successful profile access
        logger.user_journey("profile_access_success", {
            "user_type": "student",
            "email_verified": user.primary_email_verified,
            "academic_platform": "GreekSTT Research Platform"
        })
        
        logger.info(f"Profile retrieved successfully")
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@users_bp.route('/me/settings', methods=['GET'])
@jwt_required()
@verification_optional
@log_business_operation('get_user_settings_data')
def get_user_settings():
    """Get current user data for settings form (includes full email/phone for editing)."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Retrieving settings data for user {user_id}")
        
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"User not found for settings")
            return user_error_response(
                message_key='USER_NOT_FOUND',
                message_category='AUTH_MESSAGES',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        # Return full data for settings form (more sensitive)
        settings_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,  # Full email for editing
            'phone': user.phone or '',  # Full phone for editing
            'organization': user.organization or '',
            'username': user.username,
            'email_verified': user.primary_email_verified
        }
        
        logger.info(f"Settings data retrieved for user {user_id}")
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data=settings_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving settings data: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@verification_optional
@validate_request(UpdateUserSchema)
@log_business_operation('update_user_profile')
def update_current_user(validated_data):
    """Update current user profile."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Updating profile for user {user_id} with data: {list(validated_data.keys())}")
        
        # Get current user data before update to track changes
        current_user = user_service.get_user_by_id(user_id)
        if not current_user:
            logger.warning(f"User {user_id} not found for profile update")
            return user_error_response(
                message_key='USER_NOT_FOUND',
                message_category='AUTH_MESSAGES',
                error_code='USER_NOT_FOUND',
                status_code=404
            )
        
        # Capture old values for email notification
        old_values = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
            'phone': current_user.phone or '',
            'organization': current_user.organization or ''
        }
        
        user = user_service.update_user(user_id, validated_data)
        
        if not user:
            logger.warning(f"User {user_id} not found after update")
            return user_error_response(
                message_key='UPDATE_FAILED',
                error_code='UPDATE_ERROR',
                status_code=500
            )
        
        # Return full settings data after update (for form repopulation)
        updated_user_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,  # Full email for settings
            'phone': user.phone or '',  # Full phone for settings
            'organization': user.organization or '',
            'username': user.username,
            'email_verified': user.primary_email_verified
        }
        
        # Send profile updated notification email
        try:
            from app.services.email_service import email_service
            
            # Create changes list for email
            changes = []
            field_labels = {
                'first_name': 'Όνομα',
                'last_name': 'Επώνυμο', 
                'email': 'Email',
                'phone': 'Τηλέφωνο',
                'organization': 'Οργανισμός'
            }
            
            for field, new_value in validated_data.items():
                if field in field_labels and field in old_values:
                    old_value = old_values[field]
                    # Only include changes where values actually changed
                    if str(old_value) != str(new_value):
                        changes.append({
                            'field_label': field_labels[field],
                            'old_value': old_value if old_value else 'Κενό',
                            'new_value': new_value if new_value else 'Κενό'
                        })
            
            if changes:  # Only send email if there were actual changes
                email_service.send_profile_updated_email(
                    user=user,
                    changes=changes,
                    client_ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'unknown'),
                    language='el'
                )
                logger.info(f"📧 PROFILE UPDATED EMAIL SENT | user_id={user_id}")
        except Exception as email_error:
            # Don't fail the profile update if email fails
            logger.warning(f"⚠️ Failed to send profile updated email | user_id={user_id} | error={str(email_error)}")
        
        logger.info(f"Profile updated successfully for user {user_id}")
        return user_success_response(
            message_key='PROFILE_UPDATED_SUCCESSFULLY',
            data=updated_user_data
        )
        
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
@verification_optional
@validate_request(ChangePasswordSchema)
@log_business_operation('change_user_password')
def change_password(validated_data):
    """Change current user password."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Password change request for user {user_id}")
        
        if user_service.change_password(
            user_id,
            validated_data['current_password'],
            validated_data['new_password']
        ):
            # Send password changed notification email
            try:
                from app.services.email_service import email_service
                user = user_service.get_user_by_id(user_id)
                if user:
                    email_service.send_password_changed_email(
                        user=user,
                        change_type='manual',
                        client_ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', 'unknown'),
                        language='el'
                    )
                    logger.info(f"📧 PASSWORD CHANGED EMAIL SENT | user_id={user_id}")
            except Exception as email_error:
                # Don't fail the password change if email fails
                logger.warning(f"⚠️ Failed to send password changed email | user_id={user_id} | error={str(email_error)}")
            
            logger.info(f"Password changed successfully for user {user_id}")
            return user_success_response(
                message_key='PASSWORD_CHANGED_SUCCESSFULLY'
            )
        else:
            logger.warning(f"Password change failed for user {user_id}: invalid current password")
            return user_error_response(
                message_key='CURRENT_PASSWORD_INCORRECT',
                error_code='INVALID_PASSWORD',
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@users_bp.route('/me/dashboard-stats', methods=['GET'])
@jwt_required()
@verification_optional
@log_business_operation('get_user_dashboard_statistics')
def get_user_dashboard_stats():
    """Get current user dashboard statistics."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Retrieving dashboard statistics for user {user_id}")
        
        stats = user_service.get_user_stats(user_id)
        
        # Get today's completed transcriptions count
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        from app.transcription.models import Transcription
        completed_today = Transcription.query.filter(
            Transcription.user_id == user_id,
            Transcription.created_at >= today_start,
            Transcription.created_at < today_end,
            Transcription.is_deleted == False
        ).count()
        
        # Format stats for dashboard compatibility
        dashboard_stats = {
            'totalTranscriptions': stats.get('total_transcriptions', 0),
            'totalMinutesTranscribed': stats.get('total_duration_seconds', 0) / 60,  # Convert to minutes
            'totalFilesUploaded': stats.get('total_transcriptions', 0),  # For now, assume 1 file per transcription
            'averageAccuracy': 0,  # Will be calculated from analytics service
            'monthlyUsage': {
                'minutesUsed': stats.get('monthly_duration_seconds', 0) / 60,  # Convert to minutes
                'minutesLimit': -1,  # Academic version - unlimited
                'filesUploaded': stats.get('monthly_transcriptions', 0),
                'filesLimit': -1   # Academic version - unlimited
            },
            'recentActivity': {
                'completedToday': completed_today,
                'processingCount': 0,  # Could be calculated if needed
                'failedCount': 0      # Could be calculated if needed
            }
        }
        
        logger.info(f"Dashboard statistics retrieved for user {user_id}")
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={'stats': dashboard_stats}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard statistics for user {user_id}: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@users_bp.route('/stats', methods=['GET'])
@jwt_required()
@verification_required
@log_business_operation('get_user_statistics')
def get_user_stats():
    """Get current user statistics."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Retrieving statistics for user {user_id}")
        
        stats = user_service.get_user_stats(user_id)
        
        logger.info(f"Statistics retrieved for user {user_id}: {stats.get('total_transcriptions', 0)} transcriptions, {stats.get('total_duration_formatted', '0m')} total duration")
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={'stats': stats}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving statistics for user {user_id}: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )