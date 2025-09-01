"""User management schemas for request validation."""

from marshmallow import Schema, fields, validate, pre_load
import re


class UpdateUserSchema(Schema):
    """Schema for user profile updates."""
    first_name = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=False, validate=validate.Length(max=255))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))
    organization = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))


class ChangePasswordSchema(Schema):
    """Schema for password change requests."""
    current_password = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    confirm_password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    
    @pre_load
    def validate_password_change(self, in_data, **kwargs):
        """Validate password change requirements."""
        new_password = in_data.get('new_password', '')
        confirm_password = in_data.get('confirm_password', '')
        
        # Check if passwords match
        if new_password != confirm_password:
            raise ValueError("New password and confirmation do not match")
        
        # At least 8 characters, one letter, one number
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Za-z]', new_password):
            raise ValueError("Password must contain at least one letter")
            
        if not re.search(r'\d', new_password):
            raise ValueError("Password must contain at least one number")
            
        return in_data