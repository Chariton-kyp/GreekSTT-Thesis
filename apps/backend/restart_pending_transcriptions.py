#!/usr/bin/env python3
"""Script to restart pending transcriptions."""

import sys
import os
sys.path.append('/app')

from app import create_app
from app.transcription.models import Transcription
from app.transcription.services import TranscriptionService
from app.extensions import db

def restart_pending_transcriptions():
    """Restart all pending transcriptions."""
    app, _ = create_app('development')
    
    with app.app_context():
        # Get all pending transcriptions
        pending_transcriptions = Transcription.query.filter_by(status='pending').all()
        print(f"Found {len(pending_transcriptions)} pending transcriptions")
        
        if not pending_transcriptions:
            print("No pending transcriptions to restart")
            return
        
        transcription_service = TranscriptionService()
        
        for transcription in pending_transcriptions:
            try:
                print(f"Restarting transcription {transcription.id}: {transcription.title}")
                
                # Reset transcription status
                transcription.status = 'pending'
                transcription.error_message = None
                transcription.started_at = None
                transcription.completed_at = None
                db.session.commit()
                
                # Start processing
                transcription_service._process_transcription_async(transcription.id)
                print(f"✅ Restarted transcription {transcription.id}")
                
            except Exception as e:
                print(f"❌ Failed to restart transcription {transcription.id}: {str(e)}")
        
        print("All pending transcriptions have been restarted")

if __name__ == "__main__":
    restart_pending_transcriptions()