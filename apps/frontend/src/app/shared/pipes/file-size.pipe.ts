import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'fileSize',
  standalone: true
})
export class FileSizePipe implements PipeTransform {
  transform(bytes: number | null | undefined, precision: number = 1): string {
    if (bytes === null || bytes === undefined || isNaN(bytes)) {
      return '0 Bytes';
    }

    if (bytes === 0) {
      return '0 Bytes';
    }

    const k = 1024;
    const dm = precision < 0 ? 0 : precision;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }
}

@Pipe({
  name: 'fileSizeGreek',
  standalone: true
})
export class FileSizeGreekPipe implements PipeTransform {
  transform(bytes: number | null | undefined, precision: number = 1): string {
    if (bytes === null || bytes === undefined || isNaN(bytes)) {
      return '0 Bytes';
    }

    if (bytes === 0) {
      return '0 Bytes';
    }

    const k = 1024;
    const dm = precision < 0 ? 0 : precision;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const greekSizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + greekSizes[i];
  }
}