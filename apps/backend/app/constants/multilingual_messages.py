# -*- coding: utf-8 -*-
"""
Multilingual message system for GreekSTT Research Platform
Supports Greek (default) and English languages
"""

from typing import Dict, Any

class MultilingualMessages:
    """Centralized multilingual message management"""
    
    DEFAULT_LANGUAGE = 'el'
    
    # Authentication Messages
    AUTH_MESSAGES = {
        'el': {
            'EMAIL_ALREADY_REGISTERED': 'Αυτό το email είναι ήδη καταχωρημένο. Δοκιμάστε να συνδεθείτε ή να ανακτήσετε τον κωδικό σας.',
            'USERNAME_ALREADY_EXISTS': 'Αυτό το όνομα χρήστη υπάρχει ήδη. Παρακαλώ επιλέξτε ένα άλλο.',
            'REGISTRATION_SUCCESSFUL': 'Η εγγραφή ολοκληρώθηκε επιτυχώς! Ελέγξτε το email σας για επιβεβαίωση.',
            'REGISTRATION_SUCCESSFUL_NO_VERIFICATION': 'Η εγγραφή ολοκληρώθηκε επιτυχώς και συνδεθήκατε!',
            
            'INVALID_CREDENTIALS': 'Λάθος email ή κωδικός. Παρακαλώ ελέγξτε τα στοιχεία σας.',
            'LOGIN_SUCCESSFUL': 'Η σύνδεση ολοκληρώθηκε επιτυχώς!',
            'ACCOUNT_DISABLED': 'Ο λογαριασμός σας έχει απενεργοποιηθεί. Επικοινωνήστε με την υποστήριξη.',
            'EMAIL_NOT_VERIFIED': 'Παρακαλώ επιβεβαιώστε το email σας πριν συνδεθείτε.',
            
            'EMAIL_VERIFICATION_SENT': 'Κωδικός επιβεβαίωσης στάλθηκε στο email σας.',
            'EMAIL_VERIFIED_SUCCESSFULLY': 'Το email επιβεβαιώθηκε επιτυχώς!',
            'INVALID_VERIFICATION_CODE': 'Μη έγκυρος κωδικός επιβεβαίωσης.',
            'VERIFICATION_CODE_EXPIRED': 'Ο κωδικός επιβεβαίωσης έχει λήξει.',
            'EMAIL_ALREADY_VERIFIED': 'Το email είναι ήδη επιβεβαιωμένο.',
            'TOO_MANY_VERIFICATION_ATTEMPTS': 'Πολλές απόπειρες επιβεβαίωσης. Παρακαλώ περιμένετε.',
            
            'PASSWORD_RESET_SENT': 'Κωδικός επαναφοράς στάλθηκε στο email σας.',
            'PASSWORD_RESET_SUCCESSFUL': 'Ο κωδικός πρόσβασης άλλαξε επιτυχώς!',
            'RESET_CODE_VERIFIED': 'Ο κωδικός επαναφοράς επιβεβαιώθηκε επιτυχώς!',
            'INVALID_RESET_CODE': 'Μη έγκυρος κωδικός επαναφοράς.',
            'RESET_CODE_EXPIRED': 'Ο κωδικός επαναφοράς έχει λήξει.',
            'NO_CODE': 'Δεν βρέθηκε κωδικός επαναφοράς. Παρακαλώ ζητήστε νέο κωδικό επαναφοράς.',
            'USER_NOT_FOUND': 'Δεν βρέθηκε χρήστης με αυτό το email.',
            
            # General Auth
            'UNAUTHORIZED': 'Μη εξουσιοδοτημένη πρόσβαση.',
            'FORBIDDEN': 'Δεν έχετε δικαίωμα για αυτή την ενέργεια.',
            'SESSION_EXPIRED': 'Η συνεδρία έληξε. Παρακαλώ συνδεθείτε ξανά.',
            'LOGOUT_SUCCESSFUL': 'Η αποσύνδεση ολοκληρώθηκε επιτυχώς!',
            
            # JWT Token Errors
            'AUTHORIZATION_REQUIRED': 'Απαιτείται πιστοποίηση για αυτή την ενέργεια.',
            'INVALID_AUTHORIZATION_HEADER': 'Μη έγκυρη κεφαλίδα πιστοποίησης.',
            'INVALID_TOKEN': 'Μη έγκυρο token πιστοποίησης.',
            'TOKEN_EXPIRED': 'Το token πιστοποίησης έχει λήξει.',
            'TOKEN_REVOKED': 'Το token πιστοποίησης έχει ανακληθεί.',
        },
        'en': {
            # Registration
            'EMAIL_ALREADY_REGISTERED': 'This email is already registered. Try logging in or recovering your password.',
            'USERNAME_ALREADY_EXISTS': 'This username already exists. Please choose another one.',
            'REGISTRATION_SUCCESSFUL': 'Registration completed successfully! Check your email for verification.',
            'REGISTRATION_SUCCESSFUL_NO_VERIFICATION': 'Registration completed successfully and you are logged in!',
            
            # Login
            'INVALID_CREDENTIALS': 'Invalid email or password. Please check your credentials.',
            'LOGIN_SUCCESSFUL': 'Login completed successfully!',
            'ACCOUNT_DISABLED': 'Your account has been disabled. Contact support.',
            'EMAIL_NOT_VERIFIED': 'Please verify your email before logging in.',
            
            # Email Verification
            'EMAIL_VERIFICATION_SENT': 'Verification code sent to your email.',
            'EMAIL_VERIFIED_SUCCESSFULLY': 'Email verified successfully!',
            'INVALID_VERIFICATION_CODE': 'Invalid verification code.',
            'VERIFICATION_CODE_EXPIRED': 'Verification code has expired.',
            'EMAIL_ALREADY_VERIFIED': 'Email is already verified.',
            'TOO_MANY_VERIFICATION_ATTEMPTS': 'Too many verification attempts. Please wait.',
            
            # Password Reset
            'PASSWORD_RESET_SENT': 'Password reset code sent to your email.',
            'PASSWORD_RESET_SUCCESSFUL': 'Password changed successfully!',
            'RESET_CODE_VERIFIED': 'Reset code verified successfully!',
            'INVALID_RESET_CODE': 'Invalid reset code.',
            'RESET_CODE_EXPIRED': 'Reset code has expired.',
            'NO_CODE': 'No reset code found. Please request a new reset code.',
            'USER_NOT_FOUND': 'No user found with this email.',
            
            # General Auth
            'UNAUTHORIZED': 'Unauthorized access.',
            'FORBIDDEN': 'You do not have permission for this action.',
            'SESSION_EXPIRED': 'Session expired. Please log in again.',
            'LOGOUT_SUCCESSFUL': 'Logout completed successfully!',
            
            # JWT Token Errors
            'AUTHORIZATION_REQUIRED': 'Authentication required for this action.',
            'INVALID_AUTHORIZATION_HEADER': 'Invalid authorization header.',
            'INVALID_TOKEN': 'Invalid authentication token.',
            'TOKEN_EXPIRED': 'Authentication token has expired.',
            'TOKEN_REVOKED': 'Authentication token has been revoked.',
        }
    }
    
    # Validation Messages
    VALIDATION_MESSAGES = {
        'el': {
            'REQUIRED_FIELD': 'Αυτό το πεδίο είναι υποχρεωτικό.',
            'INVALID_EMAIL': 'Μη έγκυρη διεύθυνση email.',
            'INVALID_PHONE': 'Μη έγκυρος αριθμός τηλεφώνου.',
            'PASSWORD_TOO_SHORT': 'Ο κωδικός πρέπει να έχει τουλάχιστον 5 χαρακτήρες.',
            'PASSWORD_TOO_WEAK': 'Ο κωδικός πρέπει να περιέχει κεφαλαία, πεζά γράμματα και αριθμούς.',
            'USERNAME_TOO_SHORT': 'Το όνομα χρήστη πρέπει να έχει τουλάχιστον 3 χαρακτήρες.',
            'USERNAME_INVALID_CHARS': 'Το όνομα χρήστη μπορεί να περιέχει μόνο γράμματα, αριθμούς και (_).',
            'FIRST_NAME_TOO_SHORT': 'Το όνομα πρέπει να έχει τουλάχιστον 2 χαρακτήρες.',
            'LAST_NAME_TOO_SHORT': 'Το επώνυμο πρέπει να έχει τουλάχιστον 2 χαρακτήρες.',
        },
        'en': {
            'REQUIRED_FIELD': 'This field is required.',
            'INVALID_EMAIL': 'Invalid email address.',
            'INVALID_PHONE': 'Invalid phone number.',
            'PASSWORD_TOO_SHORT': 'Password must be at least 8 characters long.',
            'PASSWORD_TOO_WEAK': 'Password must contain uppercase, lowercase letters and numbers.',
            'USERNAME_TOO_SHORT': 'Username must be at least 3 characters long.',
            'USERNAME_INVALID_CHARS': 'Username can only contain letters, numbers and (_).',
            'FIRST_NAME_TOO_SHORT': 'First name must be at least 2 characters long.',
            'LAST_NAME_TOO_SHORT': 'Last name must be at least 2 characters long.',
        }
    }
    
    # File Upload Messages
    FILE_MESSAGES = {
        'el': {
            'FILE_UPLOADED_SUCCESSFULLY': 'Το αρχείο ανέβηκε επιτυχώς!',
            'FILE_TOO_LARGE': 'Το αρχείο είναι πολύ μεγάλο. Μέγιστο μέγεθος: {max_size}MB.',
            'INVALID_FILE_TYPE': 'Μη υποστηριζόμενος τύπος αρχείου.',
            'FILE_UPLOAD_ERROR': 'Σφάλμα κατά το ανέβασμα του αρχείου.',
            'FILE_NOT_FOUND': 'Το αρχείο δεν βρέθηκε.',
            'FILE_DELETED_SUCCESSFULLY': 'Το αρχείο διαγράφηκε επιτυχώς!',
        },
        'en': {
            'FILE_UPLOADED_SUCCESSFULLY': 'File uploaded successfully!',
            'FILE_TOO_LARGE': 'File is too large. Maximum size: {max_size}MB.',
            'INVALID_FILE_TYPE': 'Unsupported file type.',
            'FILE_UPLOAD_ERROR': 'Error uploading file.',
            'FILE_NOT_FOUND': 'File not found.',
            'FILE_DELETED_SUCCESSFULLY': 'File deleted successfully!',
        }
    }
    
    # Transcription Messages
    TRANSCRIPTION_MESSAGES = {
        'el': {
            'TRANSCRIPTION_STARTED': 'Η μεταγραφή ξεκίνησε!',
            'TRANSCRIPTION_COMPLETED': 'Η μεταγραφή ολοκληρώθηκε επιτυχώς!',
            'TRANSCRIPTION_FAILED': 'Η μεταγραφή απέτυχε. Παρακαλώ δοκιμάστε ξανά.',
            'TRANSCRIPTION_NOT_FOUND': 'Η μεταγραφή δεν βρέθηκε.',
            'TRANSCRIPTION_DELETED_SUCCESSFULLY': 'Η μεταγραφή διαγράφηκε επιτυχώς!',
            'TRANSCRIPTION_UPDATED_SUCCESSFULLY': 'Η μεταγραφή ενημερώθηκε επιτυχώς!',
            'TRANSCRIPTION_RETRY_STARTED': 'Η επανεκκίνηση της μεταγραφής ξεκίνησε!',
            'INSUFFICIENT_CREDITS': 'Δεν έχετε αρκετά πιστώσεις για αυτή την ενέργεια.',
            'URL_VALIDATED_SUCCESSFULLY': 'Η διεύθυνση URL επαληθεύτηκε επιτυχώς!',
        },
        'en': {
            'TRANSCRIPTION_STARTED': 'Transcription started!',
            'TRANSCRIPTION_COMPLETED': 'Transcription completed successfully!',
            'TRANSCRIPTION_FAILED': 'Transcription failed. Please try again.',
            'TRANSCRIPTION_NOT_FOUND': 'Transcription not found.',
            'TRANSCRIPTION_DELETED_SUCCESSFULLY': 'Transcription deleted successfully!',
            'TRANSCRIPTION_UPDATED_SUCCESSFULLY': 'Transcription updated successfully!',
            'TRANSCRIPTION_RETRY_STARTED': 'Transcription retry started!',
            'INSUFFICIENT_CREDITS': 'You do not have enough credits for this action.',
            'URL_VALIDATED_SUCCESSFULLY': 'URL validated successfully!',
        }
    }
    
    # User Management Messages
    USER_MESSAGES = {
        'el': {
            'PROFILE_UPDATED_SUCCESSFULLY': 'Το προφίλ ενημερώθηκε επιτυχώς!',
            'PASSWORD_CHANGED_SUCCESSFULLY': 'Ο κωδικός πρόσβασης άλλαξε επιτυχώς!',
            'USER_ACTIVATED_SUCCESSFULLY': 'Ο χρήστης ενεργοποιήθηκε επιτυχώς!',
            'USER_DEACTIVATED_SUCCESSFULLY': 'Ο χρήστης απενεργοποιήθηκε επιτυχώς!',
            'CURRENT_PASSWORD_INCORRECT': 'Ο τρέχων κωδικός είναι λάθος.',
        },
        'en': {
            'PROFILE_UPDATED_SUCCESSFULLY': 'Profile updated successfully!',
            'PASSWORD_CHANGED_SUCCESSFULLY': 'Password changed successfully!',
            'USER_ACTIVATED_SUCCESSFULLY': 'User activated successfully!',
            'USER_DEACTIVATED_SUCCESSFULLY': 'User deactivated successfully!',
            'CURRENT_PASSWORD_INCORRECT': 'Current password is incorrect.',
        }
    }
    
    # Academic Research Messages
    ACADEMIC_MESSAGES = {
        'el': {
            'ACADEMIC_ACCESS_GRANTED': 'Πρόσβαση σε ακαδημαϊκή έκδοση παραχωρήθηκε!',
            'RESEARCH_MODE_ACTIVE': 'Λειτουργία έρευνας ενεργή.',
            'UNLIMITED_ACCESS': 'Απεριόριστη πρόσβαση για ακαδημαϊκούς σκοπούς.',
            'THESIS_MODE': 'Λειτουργία διπλωματικής εργασίας.',
            'ACADEMIC_DISCLAIMER': 'Μόνο για ακαδημαϊκή χρήση.',
        },
        'en': {
            'ACADEMIC_ACCESS_GRANTED': 'Academic version access granted!',
            'RESEARCH_MODE_ACTIVE': 'Research mode active.',
            'UNLIMITED_ACCESS': 'Unlimited access for academic purposes.',
            'THESIS_MODE': 'Thesis mode.',
            'ACADEMIC_DISCLAIMER': 'For academic use only.',
        }
    }
    
    # Template Messages - removed for academic version
# Template messages removed for academic version
    
    # Voice Notes Messages
    VOICE_NOTES_MESSAGES = {
        'el': {
            'VOICE_NOTE_CREATED_SUCCESSFULLY': 'Η φωνητική σημείωση δημιουργήθηκε επιτυχώς!',
            'VOICE_NOTE_UPDATED_SUCCESSFULLY': 'Η φωνητική σημείωση ενημερώθηκε επιτυχώς!',
            'VOICE_NOTE_DELETED_SUCCESSFULLY': 'Η φωνητική σημείωση διαγράφηκε επιτυχώς!',
            'VOICE_NOTE_ARCHIVED_SUCCESSFULLY': 'Η φωνητική σημείωση αρχειοθετήθηκε επιτυχώς!',
            'VOICE_NOTE_UNARCHIVED_SUCCESSFULLY': 'Η φωνητική σημείωση επαναφέρθηκε από το αρχείο!',
            'VOICE_NOTE_NOT_FOUND': 'Η φωνητική σημείωση δεν βρέθηκε.',
            'TRANSCRIPTION_INITIATED': 'Η μεταγραφή ξεκίνησε επιτυχώς!',
            'FILE_REQUIRED': 'Απαιτείται αρχείο ήχου.',
            'TITLE_REQUIRED': 'Απαιτείται τίτλος.',
            'INVALID_FILE': 'Μη έγκυρο αρχείο ήχου.',
        },
        'en': {
            'VOICE_NOTE_CREATED_SUCCESSFULLY': 'Voice note created successfully!',
            'VOICE_NOTE_UPDATED_SUCCESSFULLY': 'Voice note updated successfully!',
            'VOICE_NOTE_DELETED_SUCCESSFULLY': 'Voice note deleted successfully!',
            'VOICE_NOTE_ARCHIVED_SUCCESSFULLY': 'Voice note archived successfully!',
            'VOICE_NOTE_UNARCHIVED_SUCCESSFULLY': 'Voice note unarchived successfully!',
            'VOICE_NOTE_NOT_FOUND': 'Voice note not found.',
            'TRANSCRIPTION_INITIATED': 'Transcription initiated successfully!',
            'FILE_REQUIRED': 'Audio file is required.',
            'TITLE_REQUIRED': 'Title is required.',
            'INVALID_FILE': 'Invalid audio file.',
        }
    }
    
    # Session Messages
    SESSION_MESSAGES = {
        'el': {
            'SESSION_TERMINATED_SUCCESSFULLY': 'Η συνεδρία τερματίστηκε επιτυχώς!',
            'ALL_SESSIONS_TERMINATED': 'Όλες οι συνεδρίες τερματίστηκαν!',
            'DEVICE_TRUSTED_SUCCESSFULLY': 'Η συσκευή επισημάνθηκε ως αξιόπιστη!',
            'SESSION_NOT_FOUND': 'Η συνεδρία δεν βρέθηκε.',
        },
        'en': {
            'SESSION_TERMINATED_SUCCESSFULLY': 'Session terminated successfully!',
            'ALL_SESSIONS_TERMINATED': 'All sessions terminated!',
            'DEVICE_TRUSTED_SUCCESSFULLY': 'Device marked as trusted!',
            'SESSION_NOT_FOUND': 'Session not found.',
        }
    }
    
    # General Error Messages
    ERROR_MESSAGES = {
        'el': {
            'INTERNAL_SERVER_ERROR': 'Εσωτερικό σφάλμα διακομιστή. Παρακαλώ δοκιμάστε αργότερα.',
            'BAD_REQUEST': 'Μη έγκυρο αίτημα.',
            'NOT_FOUND': 'Το αιτούμενο στοιχείο δεν βρέθηκε.',
            'RATE_LIMIT_EXCEEDED': 'Πολλές απόπειρες. Παρακαλώ περιμένετε πριν δοκιμάσετε ξανά.',
            'SERVICE_UNAVAILABLE': 'Η υπηρεσία δεν είναι διαθέσιμη προσωρινά.',
            'DATABASE_ERROR': 'Σφάλμα βάσης δεδομένων.',
            'VALIDATION_ERROR': 'Σφάλματα επικύρωσης δεδομένων.',
        },
        'en': {
            'INTERNAL_SERVER_ERROR': 'Internal server error. Please try again later.',
            'BAD_REQUEST': 'Bad request.',
            'NOT_FOUND': 'The requested item was not found.',
            'RATE_LIMIT_EXCEEDED': 'Too many attempts. Please wait before trying again.',
            'SERVICE_UNAVAILABLE': 'Service temporarily unavailable.',
            'DATABASE_ERROR': 'Database error.',
            'VALIDATION_ERROR': 'Data validation errors.',
        }
    }
    
    # Success Messages
    SUCCESS_MESSAGES = {
        'el': {
            'OPERATION_SUCCESSFUL': 'Η ενέργεια ολοκληρώθηκε επιτυχώς!',
            'DATA_SAVED_SUCCESSFULLY': 'Τα δεδομένα αποθηκεύτηκαν επιτυχώς!',
            'DATA_UPDATED_SUCCESSFULLY': 'Τα δεδομένα ενημερώθηκαν επιτυχώς!',
            'DATA_DELETED_SUCCESSFULLY': 'Τα δεδομένα διαγράφηκαν επιτυχώς!',
        },
        'en': {
            'OPERATION_SUCCESSFUL': 'Operation completed successfully!',
            'DATA_SAVED_SUCCESSFULLY': 'Data saved successfully!',
            'DATA_UPDATED_SUCCESSFULLY': 'Data updated successfully!',
            'DATA_DELETED_SUCCESSFULLY': 'Data deleted successfully!',
        }
    }
    
    @classmethod
    def get_message(cls, category: str, key: str, language: str = None, **kwargs) -> str:
        """
        Get a localized message
        
        Args:
            category: Message category (e.g., 'AUTH_MESSAGES', 'ERROR_MESSAGES')
            key: Message key within the category
            language: Language code ('el' or 'en'), defaults to Greek
            **kwargs: Format parameters for the message
            
        Returns:
            Localized message string
        """
        if language is None:
            language = cls.DEFAULT_LANGUAGE
            
        # Get the message category
        category_messages = getattr(cls, category, {})
        
        # Get messages for the specified language, fallback to default
        messages = category_messages.get(language, category_messages.get(cls.DEFAULT_LANGUAGE, {}))
        
        # Get the specific message, fallback to English if not found in default language
        message = messages.get(key)
        if not message and language != 'en':
            en_messages = category_messages.get('en', {})
            message = en_messages.get(key, f"Message not found: {category}.{key}")
        elif not message:
            message = f"Message not found: {category}.{key}"
            
        # Format the message with any provided parameters
        try:
            return message.format(**kwargs) if kwargs else message
        except KeyError as e:
            # If formatting fails, return the unformatted message
            return message

# Helper functions for easy access
def get_auth_message(key: str, language: str = None, **kwargs) -> str:
    """Get authentication message"""
    return MultilingualMessages.get_message('AUTH_MESSAGES', key, language, **kwargs)

def get_validation_message(key: str, language: str = None, **kwargs) -> str:
    """Get validation message"""
    return MultilingualMessages.get_message('VALIDATION_MESSAGES', key, language, **kwargs)

def get_file_message(key: str, language: str = None, **kwargs) -> str:
    """Get file operation message"""
    return MultilingualMessages.get_message('FILE_MESSAGES', key, language, **kwargs)

def get_transcription_message(key: str, language: str = None, **kwargs) -> str:
    """Get transcription message"""
    return MultilingualMessages.get_message('TRANSCRIPTION_MESSAGES', key, language, **kwargs)

def get_user_message(key: str, language: str = None, **kwargs) -> str:
    """Get user management message"""
    return MultilingualMessages.get_message('USER_MESSAGES', key, language, **kwargs)

def get_academic_message(key: str, language: str = None, **kwargs) -> str:
    """Get academic message"""
    return MultilingualMessages.get_message('ACADEMIC_MESSAGES', key, language, **kwargs)

def get_template_message(key: str, language: str = None, **kwargs) -> str:
    """Template functionality removed for academic version"""
    return "Template functionality not available in academic version"

def get_session_message(key: str, language: str = None, **kwargs) -> str:
    """Get session message"""
    return MultilingualMessages.get_message('SESSION_MESSAGES', key, language, **kwargs)

def get_error_message(key: str, language: str = None, **kwargs) -> str:
    """Get error message"""
    return MultilingualMessages.get_message('ERROR_MESSAGES', key, language, **kwargs)

def get_success_message(key: str, language: str = None, **kwargs) -> str:
    """Get success message"""
    return MultilingualMessages.get_message('SUCCESS_MESSAGES', key, language, **kwargs)