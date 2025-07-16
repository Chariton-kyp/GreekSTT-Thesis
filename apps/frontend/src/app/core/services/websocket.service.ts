import { Injectable, inject, signal } from '@angular/core';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { filter } from 'rxjs/operators';
import { io, Socket } from 'socket.io-client';
import { environment } from '../../../environments/environment';
import { TokenService } from './token.service';

export interface TranscriptionProgress {
  transcription_id: string;
  stage: string;
  percentage: number;
  message: string;
  timestamp: string;
}

export interface TranscriptionCompletion {
  transcription_id: string;
  stage: 'completed';
  percentage: 100;
  message: string;
  text_preview?: string;
  word_count?: number;
  confidence_score?: number;
  duration_seconds?: number;
  timestamp: string;
}

export interface TranscriptionError {
  transcription_id: string;
  stage: 'error';
  percentage: 0;
  message: string;
  error_code?: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private readonly tokenService = inject(TokenService);
  
  private socket: Socket | null = null;
  private isConnected = signal<boolean>(false);
  private connectionError = signal<string | null>(null);
  
  private progressSubject = new Subject<TranscriptionProgress>();
  private completionSubject = new Subject<TranscriptionCompletion>();
  private errorSubject = new Subject<TranscriptionError>();
  private connectionSubject = new BehaviorSubject<boolean>(false);
  
  readonly isConnected$ = this.connectionSubject.asObservable();
  readonly progressUpdates$ = this.progressSubject.asObservable();
  readonly completionEvents$ = this.completionSubject.asObservable();
  readonly errorEvents$ = this.errorSubject.asObservable();
  
  readonly connected = this.isConnected.asReadonly();
  readonly error = this.connectionError.asReadonly();

  connect(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      try {
        const token = this.tokenService.getAccessToken();
        
        const socketOptions: any = {
          transports: ['websocket', 'polling'],
          timeout: 10000,
          reconnection: true,
          reconnectionDelay: 2000,
          reconnectionDelayMax: 10000,
          reconnectionAttempts: Infinity,
          path: '/socket.io/',
          autoConnect: true
        };

        if (token) {
          socketOptions.auth = { token };
        }

        this.socket = io(environment.wsUrl, socketOptions);

        this.socket.on('connect', () => {
          console.log('WebSocket connected successfully');
          this.isConnected.set(true);
          this.connectionSubject.next(true);
          this.connectionError.set(null);
          resolve(true);
        });

        this.socket.on('connected', (data) => {
          console.log('Server confirmed connection:', data);
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          const errorMsg = error.message || 'Connection failed';
          this.connectionError.set(`${errorMsg} - retrying...`);
          this.isConnected.set(false);
          this.connectionSubject.next(false);
          if (!this.socket?.active) {
            reject(error);
          }
        });

        this.socket.on('auth_error', (data) => {
          console.error('WebSocket authentication error:', data);
          this.connectionError.set(data.message || 'Authentication failed');
          this.disconnect();
          reject(new Error(data.message));
        });

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          this.isConnected.set(false);
          this.connectionSubject.next(false);
          
          if (reason === 'io server disconnect') {
            this.connectionError.set('Server disconnected - attempting to reconnect...');
            this.socket?.connect();
          } else if (reason === 'transport close' || reason === 'transport error') {
            this.connectionError.set('Connection lost - reconnecting...');
          }
        });

        this.socket.on('transcription_progress', (data: TranscriptionProgress) => {
          console.log('Progress update received:', data);
          this.progressSubject.next(data);
        });

        this.socket.on('transcription_completed', (data: TranscriptionCompletion) => {
          console.log('Transcription completed:', data);
          this.completionSubject.next(data);
        });

        this.socket.on('transcription_error', (data: TranscriptionError) => {
          console.error('Transcription error:', data);
          this.errorSubject.next(data);
        });

        this.socket.on('room_joined', (data) => {
          console.log('Joined transcription room:', data);
        });

        this.socket.on('room_left', (data) => {
          console.log('Left transcription room:', data);
        });

        this.socket.on('error', (data) => {
          console.error('WebSocket error:', data);
          this.connectionError.set(data.message || 'Unknown error');
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
          console.log('WebSocket reconnected after', attemptNumber, 'attempts');
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
          console.log('WebSocket reconnection attempt', attemptNumber);
          this.connectionError.set(`Reconnecting... (attempt ${attemptNumber})`);
        });
        
        this.socket.on('reconnect_error', (error) => {
          console.error('WebSocket reconnection error:', error);
        });
        
        this.socket.on('reconnect_failed', () => {
          console.error('WebSocket reconnection failed');
          this.connectionError.set('Failed to reconnect after multiple attempts');
        });

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        this.connectionError.set('Failed to create connection');
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    this.isConnected.set(false);
    this.connectionSubject.next(false);
    this.connectionError.set(null);
  }

  joinTranscriptionRoom(transcriptionId: string): Promise<boolean> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected()) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const token = this.tokenService.getAccessToken();

      const successHandler = (data: any) => {
        if (data.transcription_id === transcriptionId) {
          this.socket?.off('room_joined', successHandler);
          this.socket?.off('error', errorHandler);
          resolve(true);
        }
      };

      const errorHandler = (data: any) => {
        this.socket?.off('room_joined', successHandler);
        this.socket?.off('error', errorHandler);
        reject(new Error(data.message || 'Failed to join room'));
      };

      this.socket.on('room_joined', successHandler);
      this.socket.on('error', errorHandler);

      const joinData: any = {
        transcription_id: transcriptionId
      };
      
      if (token) {
        joinData.token = token;
      }

      this.socket.emit('join_transcription', joinData);

      setTimeout(() => {
        this.socket?.off('room_joined', successHandler);
        this.socket?.off('error', errorHandler);
        reject(new Error('Join room timeout'));
      }, 5000);
    });
  }

  leaveTranscriptionRoom(transcriptionId: string): Promise<boolean> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected()) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const successHandler = (data: any) => {
        if (data.transcription_id === transcriptionId) {
          this.socket?.off('room_left', successHandler);
          this.socket?.off('error', errorHandler);
          resolve(true);
        }
      };

      const errorHandler = (data: any) => {
        this.socket?.off('room_left', successHandler);
        this.socket?.off('error', errorHandler);
        reject(new Error(data.message || 'Failed to leave room'));
      };

      this.socket.on('room_left', successHandler);
      this.socket.on('error', errorHandler);

      this.socket.emit('leave_transcription', {
        transcription_id: transcriptionId
      });

      setTimeout(() => {
        this.socket?.off('room_left', successHandler);
        this.socket?.off('error', errorHandler);
        reject(new Error('Leave room timeout'));
      }, 5000);
    });
  }

  getProgressUpdates(transcriptionId: string): Observable<TranscriptionProgress> {
    return this.progressUpdates$.pipe(
      filter(progress => progress.transcription_id === transcriptionId)
    );
  }

  getCompletionEvents(transcriptionId: string): Observable<TranscriptionCompletion> {
    return this.completionEvents$.pipe(
      filter(completion => completion.transcription_id === transcriptionId)
    );
  }

  getErrorEvents(transcriptionId: string): Observable<TranscriptionError> {
    return this.errorEvents$.pipe(
      filter(error => error.transcription_id === transcriptionId)
    );
  }

  ping(): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.isConnected()) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const timeout = setTimeout(() => {
        this.socket?.off('pong', pongHandler);
        reject(new Error('Ping timeout'));
      }, 5000);

      const pongHandler = (data: any) => {
        clearTimeout(timeout);
        this.socket?.off('pong', pongHandler);
        resolve(data.timestamp);
      };

      this.socket.on('pong', pongHandler);
      this.socket.emit('ping');
    });
  }

  autoConnect(): void {
    if (!this.isConnected()) {
      this.connect().catch(error => {
        console.warn('Auto-connect failed:', error);
      });
    }
  }

  getConnectionStatus(): boolean {
    return this.isConnected();
  }
}