import { Injectable, inject } from '@angular/core';
import { HttpEventType } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { tap } from 'rxjs/operators';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class ChunkedUploadService {
  private readonly api = inject(ApiService);
  private readonly CHUNK_SIZE = 10 * 1024 * 1024; // 10MB chunks for large files

  async uploadLargeFile(
    file: File,
    action: 'convert' | 'upload' = 'convert',
    onProgress?: (progress: number) => void
  ): Promise<any> {
    // Initialize upload
    const { uploadId, chunkSize } = await firstValueFrom(
      this.api.post<any>('/audio/start-chunked-upload', {
        filename: file.name,
        fileSize: file.size,
        chunkSize: this.CHUNK_SIZE
      })
    );

    // Calculate chunks
    const totalChunks = Math.ceil(file.size / chunkSize);
    
    // Upload chunks
    for (let i = 0; i < totalChunks; i++) {
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunk = file.slice(start, end);
      
      const formData = new FormData();
      formData.append('chunk', chunk);
      formData.append('uploadId', uploadId);
      formData.append('chunkIndex', i.toString());
      
      await firstValueFrom(
        this.api.upload('/audio/upload-chunk', formData, {
          showSuccessMessage: false,
          showErrorMessage: false
        }).pipe(
          tap(event => {
            if (event.type === HttpEventType.Response) {
              const progress = ((i + 1) / totalChunks) * 100;
              onProgress?.(progress);
            }
          })
        )
      );
    }

    // Complete upload
    const result = await firstValueFrom(
      this.api.post<any>('/audio/complete-chunked-upload', {
        uploadId,
        action
      })
    );

    return result.audio_file;
  }
}