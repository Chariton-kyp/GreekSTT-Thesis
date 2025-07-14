"""Authentication models."""

import secrets
import random
from datetime import datetime, timedelta
from app.extensions import db


class PasswordReset(db.Model):
    """Model for password reset with 6-digit codes."""
    
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)  # 6-digit code
    token = db.Column(db.String(255), unique=True, nullable=True)  # Optional token for URL-based reset
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    reset_type = db.Column(db.String(20), default='email')  # 'email', 'sms' for future
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='password_resets')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.code:
            self.code = self.generate_6_digit_code()
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    @staticmethod
    def generate_6_digit_code():
        """Generate a secure 6-digit reset code."""
        return f"{random.randint(100000, 999999):06d}"
    
    def is_valid(self):
        """Check if the reset code is still valid."""
        return (not self.used and 
                self.expires_at > datetime.utcnow() and 
                self.attempts < self.max_attempts)
    
    def verify_code(self, input_code):
        """Verify the input code against stored code."""
        self.attempts += 1
        
        if not self.is_valid():
            return False
            
        if self.code == input_code:
            self.used = True
            self.used_at = datetime.utcnow()
            return True
            
        return False
    
    def can_resend(self, cooldown_minutes=2):
        """Check if a new code can be sent (with cooldown)."""
        if not self.created_at:
            return True
        cooldown_time = self.created_at + timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() > cooldown_time
    
    def get_remaining_time(self):
        """Get remaining time in seconds until expiration."""
        if self.expires_at <= datetime.utcnow():
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds())
    
    def __repr__(self):
        return f'<PasswordReset user_id={self.user_id} code={self.code[:2]}** attempts={self.attempts}>'


class EmailVerification(db.Model):
    """Model for email verification with 6-digit codes."""
    
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)  # 6-digit code
    token = db.Column(db.String(255), unique=True, nullable=True)  # Optional token for URL-based verification
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verification_type = db.Column(db.String(20), default='email')  # 'email', 'sms' for future
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='email_verifications')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.code:
            self.code = self.generate_6_digit_code()
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    @staticmethod
    def generate_6_digit_code():
        """Generate a secure 6-digit verification code."""
        return f"{random.randint(100000, 999999):06d}"
    
    def is_valid(self):
        """Check if the verification code is still valid."""
        return (not self.verified and 
                self.expires_at > datetime.utcnow() and 
                self.attempts < self.max_attempts)
    
    def verify_code(self, input_code):
        """Verify the input code against stored code."""
        self.attempts += 1
        
        if not self.is_valid():
            return False
            
        if self.code == input_code:
            self.verified = True
            self.verified_at = datetime.utcnow()
            return True
            
        return False
    
    def can_resend(self, cooldown_minutes=2):
        """Check if a new code can be sent (with cooldown)."""
        if not self.created_at:
            return True
        cooldown_time = self.created_at + timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() > cooldown_time
    
    def get_remaining_time(self):
        """Get remaining time in seconds until expiration."""
        if self.expires_at <= datetime.utcnow():
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds())
    
    def __repr__(self):
        return f'<EmailVerification user_id={self.user_id} code={self.code[:2]}** attempts={self.attempts}>'


# AccountLockout model removed for thesis simplification