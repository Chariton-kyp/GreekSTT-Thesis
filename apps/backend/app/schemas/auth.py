"""Authentication schemas for request validation."""

from marshmallow import Schema, fields, validate, pre_load
import re


class LoginSchema(Schema):
    """Schema for login requests."""
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    remember_me = fields.Bool(required=False, default=False)


class RegisterSchema(Schema):
    """Schema for user registration requests."""
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))
    organization = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    
    @pre_load
    def validate_password_strength(self, in_data, **kwargs):
        """Validate password strength."""
        password = in_data.get('password', '')
        
        # At least 8 characters, one letter, one number
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Za-z]', password):
            raise ValueError("Password must contain at least one letter")
            
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
            
        return in_data


class ResetPasswordRequestSchema(Schema):
    """Schema for password reset requests."""
    email = fields.Email(required=True, validate=validate.Length(max=255))


class ResetPasswordSchema(Schema):
    """Schema for password reset with token."""
    token = fields.Str(required=True, validate=validate.Length(max=255))
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))


class EmailVerificationCodeSchema(Schema):
    """Schema for email verification code validation."""
    email = fields.Email(required=False, validate=validate.Length(max=255))  # Optional - user_id from JWT is used
    code = fields.Str(required=True, validate=validate.Length(min=6, max=6))


class PasswordResetCodeVerificationSchema(Schema):
    """Schema for password reset code verification."""
    email = fields.Email(required=True, validate=validate.Length(max=255))
    code = fields.Str(required=True, validate=validate.Length(min=6, max=6))


class ResetPasswordWithCodeSchema(Schema):
    """Schema for password reset with verification code."""
    email = fields.Email(required=True, validate=validate.Length(max=255))
    code = fields.Str(required=True, validate=validate.Length(min=6, max=6))
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    
    @pre_load
    def validate_password_strength(self, in_data, **kwargs):
        """Validate password strength."""
        password = in_data.get('new_password', '')
        
        # At least 8 characters, one letter, one number
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Za-z]', password):
            raise ValueError("Password must contain at least one letter")
            
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
            
        return in_data