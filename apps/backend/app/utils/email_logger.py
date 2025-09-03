"""Clean email logging formatter για GreekSTT Comparison Platform."""

import logging
import re
import base64
import quopri
from typing import Dict, Any, Optional
from email import message_from_string
from email.header import decode_header
from flask import g
from app.utils.correlation_logger import get_correlation_logger

# Create specialized email logger
email_logger = get_correlation_logger('email_service')


class EmailLogFormatter:
    """Clean formatter για email logging που δείχνει human-readable format."""
    
    @staticmethod
    def format_email_log(email_data: Dict[str, Any]) -> str:
        """Format email data σε clean, readable format."""
        
        # Extract key information
        recipient = email_data.get('recipient', 'unknown')
        subject = email_data.get('subject', 'No Subject')
        email_type = email_data.get('email_type', 'unknown')
        tracking_id = email_data.get('tracking_id', 'unknown')
        language = email_data.get('language', 'unknown')
        
        # Format clean output
        formatted_log = f"""
📧 EMAIL SENT
{'=' * 50}
📬 Recipient: {EmailLogFormatter._mask_email(recipient)}
📝 Subject: {subject}
🏷️  Type: {email_type}
🌍 Language: {language}
🆔 Tracking ID: {tracking_id}
{'=' * 50}
"""
        return formatted_log.strip()
    
    @staticmethod
    def format_smtp_debug(smtp_data: str) -> str:
        """Format raw SMTP debug data σε readable format."""
        
        if not smtp_data:
            return "No SMTP data to format"
        
        try:
            # Clean up the data
            lines = smtp_data.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Handle different SMTP command types
                if line.startswith('send:'):
                    # Extract email content from send command
                    content = line[5:].strip()
                    if content.startswith('b\'') and content.endswith('\''):
                        # Decode bytes string
                        try:
                            content = content[2:-1]  # Remove b' and '
                            content = content.encode().decode('unicode_escape')
                            formatted_content = EmailLogFormatter._parse_email_headers(content)
                            formatted_lines.append(f"📤 SENDING EMAIL:")
                            formatted_lines.append(formatted_content)
                        except Exception:
                            formatted_lines.append(f"📤 SENDING: {content[:100]}...")
                
                elif line.startswith('reply:') or line.startswith('data:'):
                    # Server responses
                    response = line.split(':', 1)[1].strip()
                    if 'b\'' in response:
                        try:
                            # Extract response code and message
                            match = re.search(r'\((\d+),\s*b\'([^\']+)\'\)', response)
                            if match:
                                code, message = match.groups()
                                formatted_lines.append(f"📥 SERVER: {code} - {message}")
                            else:
                                formatted_lines.append(f"📥 SERVER: {response[:50]}...")
                        except Exception:
                            formatted_lines.append(f"📥 SERVER: {response[:50]}...")
                
                elif 'Content-Type:' in line or 'Subject:' in line or 'From:' in line or 'To:' in line:
                    # Important headers
                    header_line = EmailLogFormatter._decode_header_line(line)
                    formatted_lines.append(f"📋 {header_line}")
            
            return '\n'.join(formatted_lines) if formatted_lines else "No readable SMTP data found"
            
        except Exception as e:
            return f"Error formatting SMTP data: {e}"
    
    @staticmethod
    def _parse_email_headers(content: str) -> str:
        """Parse email headers από raw content."""
        try:
            # Parse as email message
            msg = message_from_string(content)
            
            headers = []
            
            # Essential headers
            to_header = EmailLogFormatter._decode_email_header(msg.get('To', 'Unknown'))
            from_header = EmailLogFormatter._decode_email_header(msg.get('From', 'Unknown'))
            subject_header = EmailLogFormatter._decode_email_header(msg.get('Subject', 'No Subject'))
            
            headers.append(f"  📧 To: {EmailLogFormatter._mask_email(to_header)}")
            headers.append(f"  📤 From: {from_header}")
            headers.append(f"  📝 Subject: {subject_header}")
            
            # Additional useful headers
            email_type = msg.get('X-Email-Type')
            if email_type:
                headers.append(f"  🏷️  Type: {email_type}")
            
            tracking_id = msg.get('X-Tracking-ID')
            if tracking_id:
                headers.append(f"  🆔 Tracking: {tracking_id}")
            
            return '\n'.join(headers)
            
        except Exception as e:
            return f"  ⚠️  Error parsing headers: {e}"
    
    @staticmethod
    def _decode_email_header(header_value: str) -> str:
        """Decode email header που μπορεί να είναι encoded."""
        if not header_value:
            return "Unknown"
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        # Try common encodings
                        try:
                            decoded_string += part.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                decoded_string += part.decode('iso-8859-1')
                            except UnicodeDecodeError:
                                decoded_string += str(part)
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
            
        except Exception:
            return header_value[:100]  # Fallback to original
    
    @staticmethod
    def _decode_header_line(line: str) -> str:
        """Decode a header line που μπορεί να περιέχει encoded content."""
        try:
            # Handle encoded subjects and other headers
            if '=?utf-8?' in line:
                # Find and decode all encoded parts
                pattern = r'=\?utf-8\?[bq]\?([^?]+)\?='
                matches = re.findall(pattern, line, re.IGNORECASE)
                
                decoded_line = line
                for match in matches:
                    try:
                        if '=?utf-8?b?' in line.lower():
                            # Base64 encoded
                            decoded = base64.b64decode(match).decode('utf-8')
                        elif '=?utf-8?q?' in line.lower():
                            # Quoted-printable
                            decoded = quopri.decodestring(match.replace('_', ' ')).decode('utf-8')
                        else:
                            decoded = match
                        
                        # Replace in the line
                        encoded_part = f"=?utf-8?{'b' if '=?utf-8?b?' in line.lower() else 'q'}?{match}?="
                        decoded_line = decoded_line.replace(encoded_part, decoded)
                    except Exception:
                        continue
                
                return decoded_line
            
            # Handle Greek characters in byte format
            if '\\x' in line:
                try:
                    # Try to decode hex sequences
                    decoded = line.encode().decode('unicode_escape')
                    return decoded
                except Exception:
                    pass
            
            return line
            
        except Exception:
            return line[:100]  # Fallback
    
    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email για privacy στα logs."""
        if not email or '@' not in email:
            return email
        
        try:
            local, domain = email.split('@', 1)
            if len(local) == 1:
                # 1 char: show first char + 2 stars
                masked_local = local[0] + '**'
            elif len(local) == 2:
                # 2 chars: show both + 2 stars
                masked_local = local + '**'
            elif len(local) == 3:
                # 3 chars: show first 2 + star
                masked_local = local[:2] + '*'
            else:
                # 4+ chars: show first 2 + stars + last 2
                stars_count = len(local) - 4
                masked_local = local[:2] + '*' * max(2, stars_count) + local[-2:]
            
            return f"{masked_local}@{domain}"
        except Exception:
            return "***@***.com"


def log_email_send_start(recipient: str, email_type: str, subject: str, language: str = 'el') -> str:
    """Log the start of email sending process."""
    tracking_id = getattr(g, 'email_tracking_id', 'unknown')
    
    email_data = {
        'recipient': recipient,
        'email_type': email_type,
        'subject': subject,
        'language': language,
        'tracking_id': tracking_id
    }
    
    formatted_log = EmailLogFormatter.format_email_log(email_data)
    email_logger.info("Email send process started")
    email_logger.info(formatted_log)
    
    return tracking_id


def log_email_send_success(recipient: str, tracking_id: str, email_type: str):
    """Log successful email send."""
    email_logger.info(f"✅ Email sent successfully")
    email_logger.info(f"📧 Recipient: {EmailLogFormatter._mask_email(recipient)}")
    email_logger.info(f"🆔 Tracking ID: {tracking_id}")
    
    
def log_email_send_failure(recipient: str, tracking_id: str, error: str, email_type: str):
    """Log failed email send."""
    email_logger.error(f"❌ Email send failed")
    email_logger.error(f"📧 Recipient: {EmailLogFormatter._mask_email(recipient)}")
    email_logger.error(f"🆔 Tracking ID: {tracking_id}")
    email_logger.error(f"⚠️  Error: {error}")
    

def log_smtp_debug_clean(smtp_data: str):
    """Log SMTP debug data σε clean format."""
    if not smtp_data:
        return
    
    formatted_data = EmailLogFormatter.format_smtp_debug(smtp_data)
    email_logger.debug("📡 SMTP Communication:")
    email_logger.debug(formatted_data)


def log_email_tracking_event(tracking_id: str, event_type: str, additional_data: Optional[Dict[str, Any]] = None):
    """Log email tracking events (opened, clicked, etc.)."""
    email_logger.info(f"📊 Email tracking event: {event_type}")
    email_logger.info(f"🆔 Tracking ID: {tracking_id}")
    
    if additional_data:
        email_logger.info(f"📋 Data: {additional_data}")
        

# Convenience function for overall email analytics logging
def log_email_analytics(analytics_data: Dict[str, Any]):
    """Log email analytics summary."""
    email_logger.info("📈 Email Analytics Summary:")
    email_logger.info(f"📧 Total Sent: {analytics_data.get('total_sent', 0)}")
    email_logger.info(f"📂 Total Opened: {analytics_data.get('total_opened', 0)}")
    email_logger.info(f"🖱️  Total Clicked: {analytics_data.get('total_clicked', 0)}")
    email_logger.info(f"📊 Open Rate: {analytics_data.get('open_rate', 0):.1f}%")
    email_logger.info(f"📊 Click Rate: {analytics_data.get('click_rate', 0):.1f}%")