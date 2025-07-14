# -*- coding: utf-8 -*-
"""
Greek language messages for the GreekSTT Research Platform application.
All user-facing messages should use these constants to ensure consistency.
"""

# Authentication Messages
AUTH_MESSAGES = {
    # Registration
    'EMAIL_ALREADY_REGISTERED': 'Αυτό το email είναι ήδη καταχωρημένο. Δοκιμάστε να συνδεθείτε ή να ανακτήσετε τον κωδικό σας.',
    'USERNAME_ALREADY_EXISTS': 'Αυτό το όνομα χρήστη υπάρχει ήδη. Παρακαλώ επιλέξτε ένα άλλο.',
    'REGISTRATION_SUCCESSFUL': 'Η εγγραφή ολοκληρώθηκε επιτυχώς! Ελέγξτε το email σας για επιβεβαίωση.',
    'REGISTRATION_SUCCESSFUL_NO_VERIFICATION': 'Η εγγραφή ολοκληρώθηκε επιτυχώς και συνδεθήκατε!',
    
    # Login
    'INVALID_CREDENTIALS': 'Λάθος email ή κωδικός. Παρακαλώ ελέγξτε τα στοιχεία σας.',
    'LOGIN_SUCCESSFUL': 'Η σύνδεση ολοκληρώθηκε επιτυχώς!',
    'ACCOUNT_DISABLED': 'Ο λογαριασμός σας έχει απενεργοποιηθεί. Επικοινωνήστε με την υποστήριξη.',
    'EMAIL_NOT_VERIFIED': 'Παρακαλώ επιβεβαιώστε το email σας πριν συνδεθείτε.',
    
    # Email Verification
    'EMAIL_VERIFICATION_SENT': 'Κωδικός επιβεβαίωσης στάλθηκε στο email σας.',
    'EMAIL_VERIFIED_SUCCESSFULLY': 'Το email επιβεβαιώθηκε επιτυχώς!',
    'INVALID_VERIFICATION_CODE': 'Μη έγκυρος κωδικός επιβεβαίωσης.',
    'VERIFICATION_CODE_EXPIRED': 'Ο κωδικός επιβεβαίωσης έχει λήξει.',
    'EMAIL_ALREADY_VERIFIED': 'Το email είναι ήδη επιβεβαιωμένο.',
    'TOO_MANY_VERIFICATION_ATTEMPTS': 'Πολλές απόπειρες επιβεβαίωσης. Παρακαλώ περιμένετε.',
    
    # Password Reset
    'PASSWORD_RESET_SENT': 'Κωδικός επαναφοράς στάλθηκε στο email σας.',
    'PASSWORD_RESET_SUCCESSFUL': 'Ο κωδικός πρόσβασης άλλαξε επιτυχώς!',
    'RESET_CODE_VERIFIED': 'Ο κωδικός επαναφοράς επιβεβαιώθηκε! Μπορείτε τώρα να δημιουργήσετε νέο κωδικό πρόσβασης.',
    'INVALID_RESET_CODE': 'Μη έγκυρος κωδικός επαναφοράς.',
    'RESET_CODE_EXPIRED': 'Ο κωδικός επαναφοράς έχει λήξει.',
    'USER_NOT_FOUND': 'Δεν βρέθηκε χρήστης με αυτό το email.',
    
    # General Auth
    'UNAUTHORIZED': 'Μη εξουσιοδοτημένη πρόσβαση.',
    'FORBIDDEN': 'Δεν έχετε δικαίωμα για αυτή την ενέργεια.',
    'SESSION_EXPIRED': 'Η συνεδρία έληξε. Παρακαλώ συνδεθείτε ξανά.',
    'LOGOUT_SUCCESSFUL': 'Η αποσύνδεση ολοκληρώθηκε επιτυχώς!',
}

# Validation Messages
VALIDATION_MESSAGES = {
    'REQUIRED_FIELD': 'Αυτό το πεδίο είναι υποχρεωτικό.',
    'INVALID_EMAIL': 'Μη έγκυρη διεύθυνση email.',
    'INVALID_PHONE': 'Μη έγκυρος αριθμός τηλεφώνου.',
    'PASSWORD_TOO_SHORT': 'Ο κωδικός πρέπει να έχει τουλάχιστον 5 χαρακτήρες.',
    'PASSWORD_TOO_WEAK': 'Ο κωδικός πρέπει να περιέχει κεφαλαία, πεζά γράμματα και αριθμούς.',
    'USERNAME_TOO_SHORT': 'Το όνομα χρήστη πρέπει να έχει τουλάχιστον 3 χαρακτήρες.',
    'USERNAME_INVALID_CHARS': 'Το όνομα χρήστη μπορεί να περιέχει μόνο γράμματα, αριθμούς και (_).',
    'FIRST_NAME_TOO_SHORT': 'Το όνομα πρέπει να έχει τουλάχιστον 2 χαρακτήρες.',
    'LAST_NAME_TOO_SHORT': 'Το επώνυμο πρέπει να έχει τουλάχιστον 2 χαρακτήρες.',
}

# File Upload Messages
FILE_MESSAGES = {
    'FILE_UPLOADED_SUCCESSFULLY': 'Το αρχείο ανέβηκε επιτυχώς!',
    'FILE_TOO_LARGE': 'Το αρχείο είναι πολύ μεγάλο. Μέγιστο μέγεθος: {max_size}MB.',
    'INVALID_FILE_TYPE': 'Μη υποστηριζόμενος τύπος αρχείου.',
    'FILE_UPLOAD_ERROR': 'Σφάλμα κατά το ανέβασμα του αρχείου.',
    'FILE_NOT_FOUND': 'Το αρχείο δεν βρέθηκε.',
    'FILE_DELETED_SUCCESSFULLY': 'Το αρχείο διαγράφηκε επιτυχώς!',
}

# Transcription Messages
TRANSCRIPTION_MESSAGES = {
    'TRANSCRIPTION_STARTED': 'Η μεταγραφή ξεκίνησε!',
    'TRANSCRIPTION_COMPLETED': 'Η μεταγραφή ολοκληρώθηκε επιτυχώς!',
    'TRANSCRIPTION_FAILED': 'Η μεταγραφή απέτυχε. Παρακαλώ δοκιμάστε ξανά.',
    'TRANSCRIPTION_NOT_FOUND': 'Η μεταγραφή δεν βρέθηκε.',
    'TRANSCRIPTION_DELETED_SUCCESSFULLY': 'Η μεταγραφή διαγράφηκε επιτυχώς!',
    'INSUFFICIENT_CREDITS': 'Δεν έχετε αρκετά πιστώσεις για αυτή την ενέργεια.',
}

# General Error Messages
ERROR_MESSAGES = {
    'INTERNAL_SERVER_ERROR': 'Εσωτερικό σφάλμα διακομιστή. Παρακαλώ δοκιμάστε αργότερα.',
    'BAD_REQUEST': 'Μη έγκυρο αίτημα.',
    'NOT_FOUND': 'Το αιτούμενο στοιχείο δεν βρέθηκε.',
    'RATE_LIMIT_EXCEEDED': 'Πολλές απόπειρες. Παρακαλώ περιμένετε πριν δοκιμάσετε ξανά.',
    'SERVICE_UNAVAILABLE': 'Η υπηρεσία δεν είναι διαθέσιμη προσωρινά.',
    'DATABASE_ERROR': 'Σφάλμα βάσης δεδομένων.',
    'VALIDATION_ERROR': 'Σφάλματα επικύρωσης δεδομένων.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'OPERATION_SUCCESSFUL': 'Η ενέργεια ολοκληρώθηκε επιτυχώς!',
    'DATA_SAVED_SUCCESSFULLY': 'Τα δεδομένα αποθηκεύτηκαν επιτυχώς!',
    'DATA_UPDATED_SUCCESSFULLY': 'Τα δεδομένα ενημερώθηκαν επιτυχώς!',
    'DATA_DELETED_SUCCESSFULLY': 'Τα δεδομένα διαγράφηκαν επιτυχώς!',
}