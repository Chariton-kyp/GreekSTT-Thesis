"""GreekSTT Research Platform email service for academic demo with MailHog."""

import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from flask import current_app, g
from flask_mail import Message
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON

from app.extensions import db, mail
from app.utils.email_logger import (
    log_email_send_start, 
    log_email_send_success, 
    log_email_send_failure,
    log_email_tracking_event,
    log_smtp_debug_clean
)

logger = logging.getLogger(__name__)


class EmailType(Enum):
    """Email type enumeration for tracking."""
    VERIFICATION = "verification"
    VERIFICATION_SUCCESS = "verification_success"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    NOTIFICATION = "notification"
    MARKETING = "marketing"


class EmailStatus(Enum):
    """Email status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"


@dataclass
class EmailTemplate:
    """Email template data structure."""
    subject: str
    html_content: str
    text_content: str
    variables: Dict[str, Any]


class EmailLog(db.Model):
    """Model for tracking email sending and analytics."""
    
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    recipient_email = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default=EmailStatus.PENDING.value)
    language = db.Column(db.String(5), default='el')  # 'el' for Greek, 'en' for English
    
    # Analytics
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    bounced_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    provider = db.Column(db.String(50), nullable=True)  # SMTP, MailHog for academic demo
    provider_message_id = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    email_metadata = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.tracking_id} {self.email_type} {self.status}>'


class EmailService:
    """GreekSTT Research Platform email service for academic demo with MailHog."""
    
    def __init__(self):
        self.templates = None  # Load templates lazily when needed
        self.retry_delays = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
    
    def send_verification_email(self, user, code: str, language: str = 'el') -> Dict[str, Any]:
        """Send verification email with 6-digit code."""
        template = self._get_template('verification', language)
        
        variables = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'verification_code': code,
            'expiry_minutes': 10,
            'dashboard_url': f"{current_app.config['FRONTEND_URL']}/app/dashboard",
            'company_name': 'GreekSTT Research Platform',
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'research@greekstt.local'),
            'year': datetime.now().year
        }
        
        return self._send_templated_email(
            recipient=user.email,
            user_id=user.id,
            email_type=EmailType.VERIFICATION,
            template=template,
            variables=variables,
            language=language
        )
    
    def send_password_reset_email(self, user, code: str, language: str = 'el') -> Dict[str, Any]:
        """Send password reset email with 6-digit code."""
        template = self._get_template('password_reset', language)
        
        variables = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'reset_code': code,
            'expiry_minutes': 10,
            'dashboard_url': f"{current_app.config['FRONTEND_URL']}/app/dashboard",
            'company_name': 'GreekSTT Research Platform',
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'research@greekstt.local'),
            'year': datetime.now().year
        }
        
        return self._send_templated_email(
            recipient=user.email,
            user_id=user.id,
            email_type=EmailType.PASSWORD_RESET,
            template=template,
            variables=variables,
            language=language
        )
    
    def send_welcome_email(self, user, language: str = 'el') -> Dict[str, Any]:
        """Send welcome email after successful verification."""
        template = self._get_template('welcome', language)
        
        variables = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'dashboard_url': f"{current_app.config['FRONTEND_URL']}/app/dashboard",
            'transcription_url': f"{current_app.config['FRONTEND_URL']}/app/transcription/create",
            'company_name': 'GreekSTT Research Platform',
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'research@greekstt.local'),
            'year': datetime.now().year
        }
        
        return self._send_templated_email(
            recipient=user.email,
            user_id=user.id,
            email_type=EmailType.WELCOME,
            template=template,
            variables=variables,
            language=language
        )
    
    def send_password_changed_email(self, user, change_type: str = 'manual', client_ip: str = 'unknown', user_agent: str = 'unknown', language: str = 'el') -> Dict[str, Any]:
        """Send password changed confirmation email."""
        template = self._get_template('password_changed', language)
        
        # Parse user agent to get readable browser name
        parsed_user_agent = self._parse_user_agent(user_agent)
        
        variables = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'change_datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'change_type': 'Μη αυτόματη αλλαγή' if change_type == 'manual' else 'Επαναφορά κωδικού',
            'client_ip': client_ip,
            'user_agent': parsed_user_agent,
            'dashboard_url': f"{current_app.config['FRONTEND_URL']}/app/dashboard",
            'company_name': 'GreekSTT Research Platform',
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'research@greekstt.local'),
            'year': datetime.now().year
        }
        
        return self._send_templated_email(
            recipient=user.email,
            user_id=user.id,
            email_type=EmailType.NOTIFICATION,
            template=template,
            variables=variables,
            language=language
        )
    
    def send_profile_updated_email(self, user, changes: list, client_ip: str = 'unknown', user_agent: str = 'unknown', language: str = 'el') -> Dict[str, Any]:
        """Send profile updated confirmation email."""
        template = self._get_template('profile_updated', language)
        
        # Parse user agent to get readable browser name
        parsed_user_agent = self._parse_user_agent(user_agent)
        
        variables = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'changes': changes,
            'total_changes': len(changes),
            'change_datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'client_ip': client_ip,
            'user_agent': parsed_user_agent,
            'dashboard_url': f"{current_app.config['FRONTEND_URL']}/app/dashboard",
            'company_name': 'GreekSTT Research Platform',
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'research@greekstt.local'),
            'year': datetime.now().year
        }
        
        return self._send_templated_email(
            recipient=user.email,
            user_id=user.id,
            email_type=EmailType.NOTIFICATION,
            template=template,
            variables=variables,
            language=language
        )
    
    def _send_templated_email(self, recipient: str, email_type: EmailType, 
                            template: EmailTemplate, variables: Dict[str, Any],
                            user_id: Optional[int] = None, language: str = 'el') -> Dict[str, Any]:
        """Send templated email with tracking and optimization."""
        
        # Render subject early for logging
        subject = self._render_template(template.subject, variables)
        
        # Create email log entry
        email_log = EmailLog(
            recipient_email=recipient,
            user_id=user_id,
            email_type=email_type.value,
            subject=subject,
            language=language,
            email_metadata={'variables': variables}
        )
        db.session.add(email_log)
        db.session.commit()
        
        # Set tracking ID in flask g for correlation
        g.email_tracking_id = email_log.tracking_id
        
        # Log email send start with clean formatting
        log_email_send_start(
            recipient=recipient,
            email_type=email_type.value,
            subject=subject,
            language=language
        )
        
        try:
            # Render email content (subject already rendered above)
            html_content = self._render_template(template.html_content, variables)
            text_content = self._render_template(template.text_content, variables)
            
            # Add tracking pixel to HTML content
            tracking_pixel = self._generate_tracking_pixel(email_log.tracking_id)
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
            
            # Create Flask-Mail message
            msg = Message(
                subject=subject,
                recipients=[recipient],
                html=html_content,
                body=text_content
            )
            
            # Add custom headers for better deliverability
            msg.extra_headers = {
                'X-Email-Type': email_type.value,
                'X-Tracking-ID': email_log.tracking_id,
                'List-Unsubscribe': f"<{current_app.config['FRONTEND_URL']}/unsubscribe?token={email_log.tracking_id}>",
                'X-Mailer': 'GreekSTT Academic Email Service v1.0'
            }
            
            # Send email with retry logic
            success = self._send_with_retry(msg, email_log)
            
            if success:
                email_log.status = EmailStatus.SENT.value
                email_log.sent_at = datetime.utcnow()
                db.session.commit()
                
                # Log success with clean formatting
                log_email_send_success(
                    recipient=recipient,
                    tracking_id=email_log.tracking_id,
                    email_type=email_type.value
                )
                
                return {
                    'success': True,
                    'tracking_id': email_log.tracking_id,
                    'message': f'Email sent successfully to {recipient}'
                }
            else:
                email_log.status = EmailStatus.FAILED.value
                db.session.commit()
                return {
                    'success': False,
                    'error': 'Failed to send email after retries',
                    'tracking_id': email_log.tracking_id
                }
                
        except Exception as e:
            # Log failure with clean formatting  
            log_email_send_failure(
                recipient=recipient,
                tracking_id=email_log.tracking_id,
                error=str(e),
                email_type=email_type.value
            )
            
            email_log.status = EmailStatus.FAILED.value
            email_log.error_message = str(e)
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e),
                'tracking_id': email_log.tracking_id
            }
    
    def _send_with_retry(self, msg: Message, email_log: EmailLog) -> bool:
        """Send email with retry logic."""
        for attempt in range(len(self.retry_delays) + 1):
            try:
                mail.send(msg)
                return True
            except Exception as e:
                if attempt < len(self.retry_delays):
                    delay = self.retry_delays[attempt]
                    time.sleep(delay)
                    continue
                else:
                    email_log.error_message = str(e)
                    db.session.commit()
                    return False
    
    def track_email_opened(self, tracking_id: str) -> bool:
        """Track email open event."""
        email_log = EmailLog.query.filter_by(tracking_id=tracking_id).first()
        if email_log and not email_log.opened_at:
            email_log.opened_at = datetime.utcnow()
            email_log.status = EmailStatus.OPENED.value
            db.session.commit()
            
            # Log email tracking event
            log_email_tracking_event(tracking_id, 'opened', {
                'email_type': email_log.email_type,
                'recipient': email_log.recipient_email
            })
            
            return True
        return False
    
    def track_email_clicked(self, tracking_id: str, link_url: str) -> bool:
        """Track email click event."""
        email_log = EmailLog.query.filter_by(tracking_id=tracking_id).first()
        if email_log:
            if not email_log.clicked_at:
                email_log.clicked_at = datetime.utcnow()
                email_log.status = EmailStatus.CLICKED.value
            
            # Track click in metadata
            email_log.email_metadata = email_log.email_metadata or {}
            clicks = email_log.email_metadata.get('clicks', [])
            clicks.append({
                'url': link_url,
                'timestamp': datetime.utcnow().isoformat()
            })
            email_log.email_metadata['clicks'] = clicks
            db.session.commit()
            
            # Log email tracking event
            log_email_tracking_event(tracking_id, 'clicked', {
                'email_type': email_log.email_type,
                'recipient': email_log.recipient_email,
                'link_url': link_url
            })
            
            return True
        return False
    
    def get_email_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get email analytics for the specified period."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        total_sent = EmailLog.query.filter(EmailLog.sent_at >= since_date).count()
        total_opened = EmailLog.query.filter(EmailLog.opened_at >= since_date).count()
        total_clicked = EmailLog.query.filter(EmailLog.clicked_at >= since_date).count()
        total_bounced = EmailLog.query.filter(EmailLog.bounced_at >= since_date).count()
        
        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
        
        # Get stats by email type
        type_stats = {}
        for email_type in EmailType:
            type_count = EmailLog.query.filter(
                EmailLog.email_type == email_type.value,
                EmailLog.sent_at >= since_date
            ).count()
            type_stats[email_type.value] = type_count
        
        analytics_data = {
            'period_days': days,
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_bounced': total_bounced,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'bounce_rate': round(bounce_rate, 2),
            'by_type': type_stats
        }
        
        # Log analytics access with clean formatting
        from app.utils.email_logger import log_email_analytics
        log_email_analytics(analytics_data)
        
        return analytics_data
    
    def _generate_tracking_pixel(self, tracking_id: str) -> str:
        """Generate tracking pixel HTML for email open tracking."""
        tracking_url = f"{current_app.config['BACKEND_URL']}/analytics/email-open/{tracking_id}"
        return f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="">'
    
    def _render_template(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render template string with variables using Jinja2."""
        try:
            from jinja2 import Template
            template = Template(template_string)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            # Fallback to simple string replacement
            for key, value in variables.items():
                # Handle both formats: {{key}} and {{ key }}
                placeholder_no_space = f"{{{{{key}}}}}"
                placeholder_with_space = f"{{{{ {key} }}}}"
                template_string = template_string.replace(placeholder_no_space, str(value))
                template_string = template_string.replace(placeholder_with_space, str(value))
            return template_string
    
    def _parse_user_agent(self, user_agent: str) -> str:
        """Parse user agent string to extract readable browser and OS info."""
        if not user_agent or user_agent == 'unknown':
            return 'Άγνωστος Φυλλομετρητής'
        
        try:
            from user_agents import parse
            parsed_ua = parse(user_agent)
            
            # Get browser name
            browser = parsed_ua.browser.family or 'Άγνωστος Φυλλομετρητής'
            if browser == 'Chrome':
                browser = 'Chrome'
            elif browser == 'Firefox':
                browser = 'Firefox'
            elif browser == 'Safari':
                browser = 'Safari'
            elif browser == 'Edge':
                browser = 'Microsoft Edge'
            elif browser == 'Opera':
                browser = 'Opera'
            
            # Get OS name
            os_name = parsed_ua.os.family or 'Άγνωστο Σύστημα'
            if 'Windows' in os_name:
                os_name = 'Windows'
            elif 'Mac OS X' in os_name or 'macOS' in os_name:
                os_name = 'macOS'
            elif 'Linux' in os_name:
                os_name = 'Linux'
            elif 'Android' in os_name:
                os_name = 'Android'
            elif 'iOS' in os_name:
                os_name = 'iOS'
            
            return f"{browser} στο {os_name}"
            
        except Exception as e:
            logger.warning(f"Failed to parse user agent: {str(e)}")
            # Fallback to truncated user agent
            return user_agent[:50] + '...' if len(user_agent) > 50 else user_agent
    
    def _get_template(self, template_name: str, language: str) -> EmailTemplate:
        """Get email template by name and language."""
        if self.templates is None:
            self.templates = self._load_templates()
        return self.templates[language][template_name]
    
    def _load_templates(self) -> Dict[str, Dict[str, EmailTemplate]]:
        """Load email templates for all languages."""
        return {
            'el': self._load_greek_templates(),
            'en': self._load_english_templates()
        }
    
    def _load_greek_templates(self) -> Dict[str, EmailTemplate]:
        """Load Greek email templates."""
        return {
            'verification': EmailTemplate(
                subject="Επαλήθευση Email - {{ company_name }}",
                html_content=self._load_template_file('email_verification.html'),
                text_content=self._get_greek_verification_text(),
                variables={}
            ),
            'password_reset': EmailTemplate(
                subject="Επαναφορά Κωδικού - {{ company_name }}",
                html_content=self._load_template_file('password_reset.html'),
                text_content=self._get_greek_reset_text(),
                variables={}
            ),
            'welcome': EmailTemplate(
                subject="Καλώς ήρθατε στο {{ company_name }}!",
                html_content=self._load_template_file('welcome.html'),
                text_content=self._get_greek_welcome_text(),
                variables={}
            ),
            'password_changed': EmailTemplate(
                subject="Κωδικός Ενημερώθηκε - {{ company_name }}",
                html_content=self._load_template_file('password_changed.html'),
                text_content=self._get_greek_password_changed_text(),
                variables={}
            ),
            'profile_updated': EmailTemplate(
                subject="Προφίλ Ενημερώθηκε - {{ company_name }}",
                html_content=self._load_template_file('profile_updated.html'),
                text_content=self._get_greek_profile_updated_text(),
                variables={}
            )
        }
    
    def _load_english_templates(self) -> Dict[str, EmailTemplate]:
        """Load English email templates (minimal fallback for now)."""
        return {
            'verification': EmailTemplate(
                subject="Email Verification - {{ company_name }}",
                html_content=self._load_template_file('email_verification.html'),  # Same template for now
                text_content=self._get_greek_verification_text(),  # Fallback to Greek
                variables={}
            ),
            'password_reset': EmailTemplate(
                subject="Password Reset - {{ company_name }}",
                html_content=self._load_template_file('password_reset.html'),
                text_content=self._get_greek_reset_text(),
                variables={}
            ),
            'welcome': EmailTemplate(
                subject="Welcome to {{ company_name }}!",
                html_content=self._load_template_file('welcome.html'),
                text_content=self._get_greek_welcome_text(),
                variables={}
            ),
            'password_changed': EmailTemplate(
                subject="Password Updated - {{ company_name }}",
                html_content=self._load_template_file('password_changed.html'),
                text_content=self._get_greek_password_changed_text(),
                variables={}
            ),
            'profile_updated': EmailTemplate(
                subject="Profile Updated - {{ company_name }}",
                html_content=self._load_template_file('profile_updated.html'),
                text_content=self._get_greek_profile_updated_text(),
                variables={}
            )
        }
    
    def _load_template_file(self, filename: str) -> str:
        """Load email template from file with fallback paths."""
        import os
        
        # Try multiple paths for development and production
        template_paths = [
            f'/app/app/templates/emails/{filename}',  # Docker container path
            os.path.join(os.path.dirname(__file__), '..', 'templates', 'emails', filename),  # Relative path
            os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'templates', 'emails', filename)  # Alternative relative path
        ]
        
        for template_path in template_paths:
            try:
                template_path = os.path.abspath(template_path)
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception as e:
                continue
        
        # Fallback template if file not found
        return f"""
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <title>GreekSTT Research Platform Email</title>
</head>
<body>
    <h1>{{{{ company_name }}}}</h1>
    <p>Γεια σας {{{{ user_name }}}},</p>
    <p>Αυτό είναι ένα email από το {{{{ company_name }}}}.</p>
    <p>Template file {filename} δεν βρέθηκε.</p>
</body>
</html>
        """
    
    # Text templates for all email types
    def _get_greek_verification_text(self) -> str:
        """Greek verification email text template."""
        return """
{{ company_name }} - Επαλήθευση Email

Γεια σας {{ user_name }},

Καλώς ήρθατε στο {{ company_name }}! Για να ολοκληρώσετε την εγγραφή σας, παρακαλούμε επαληθεύστε τη διεύθυνση email σας.

Κωδικός Επαλήθευσης: {{ verification_code }}

Ο κωδικός λήγει σε {{ expiry_minutes }} λεπτά.

Εισάγετε αυτόν τον κωδικό στην οθόνη επαλήθευσης για να επιβεβαιώσετε το email σας.

Αν δεν δημιουργήσατε λογαριασμό, παρακαλούμε αγνοήστε αυτό το μήνυμα.

{{ company_name }}
{{ support_email }}
        """
    
    def _get_greek_reset_text(self) -> str:
        """Greek password reset email text template."""
        return """
{{ company_name }} - Επαναφορά Κωδικού

Γεια σας {{ user_name }},

Λάβαμε αίτημα για επαναφορά του κωδικού πρόσβασης του λογαριασμού σας.

Κωδικός Επαναφοράς: {{ reset_code }}

Ο κωδικός λήγει σε {{ expiry_minutes }} λεπτά.

Εισάγετε αυτόν τον κωδικό στη φόρμα επαναφοράς για να συνεχίσετε.

Αν δεν ζητήσατε επαναφορά κωδικού, παρακαλούμε αγνοήστε αυτό το email.

{{ company_name }}
{{ support_email }}
        """
    
    def _get_greek_welcome_text(self) -> str:
        """Greek welcome email text template."""
        return """
{{ company_name }} - Καλώς ήρθατε!

Γεια σας {{ user_name }},

Σας ευχαριστούμε που επιλέξατε το {{ company_name }}! Ο λογαριασμός σας έχει επαληθευτεί επιτυχώς.

Μπορείτε τώρα να:
• Μεταγράφετε ήχο σε κείμενο με υψηλή ακρίβεια
• Χρησιμοποιήσετε εξειδικευμένα πρότυπα
• Διαχειριστείτε τις μεταγραφές σας
• Έχετε πρόσβαση σε 24/7 υποστήριξη

Πίνακας Ελέγχου: {{ dashboard_url }}

Για βοήθεια: {{ support_email }}

{{ company_name }}
        """
    
    def _get_greek_password_changed_text(self) -> str:
        """Greek password changed email text template."""
        return """
{{ company_name }} - Κωδικός Ενημερώθηκε

Γεια σας {{ user_name }},

Ο κωδικός πρόσβασης για τον λογαριασμό σας στο {{ company_name }} άλλαξε επιτυχώς στις {{ change_datetime }}.

Λεπτομέρειες:
• Ημερομηνία: {{ change_datetime }}
• IP: {{ client_ip }}
• Τύπος: {{ change_type }}

Αν δεν κάνατε εσείς αυτή την αλλαγή, επικοινωνήστε άμεσα μαζί μας.

Υποστήριξη: {{ support_email }}
{{ company_name }}
        """
    
    def _get_greek_profile_updated_text(self) -> str:
        """Greek profile updated email text template."""
        return """
{{ company_name }} - Προφίλ Ενημερώθηκε

Γεια σας {{ user_name }},

Το προφίλ σας στο {{ company_name }} ενημερώθηκε επιτυχώς στις {{ change_datetime }}.

Έγιναν {{ total_changes }} αλλαγές στον λογαριασμό σας.

Λεπτομέρειες:
• Ημερομηνία: {{ change_datetime }}
• IP: {{ client_ip }}
• Συσκευή: {{ user_agent }}

Αν δεν κάνατε εσείς αυτές τις αλλαγές, επικοινωνήστε άμεσα μαζί μας.

Προφίλ: {{ dashboard_url }}/profile/settings
Υποστήριξη: {{ support_email }}

{{ company_name }}
        """


# Create a global instance
email_service = EmailService()