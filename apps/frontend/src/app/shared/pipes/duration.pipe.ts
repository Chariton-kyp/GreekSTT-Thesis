import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'duration',
  standalone: true
})
export class DurationPipe implements PipeTransform {
  transform(seconds: number | null | undefined, format: 'short' | 'long' = 'short'): string {
    if (seconds === null || seconds === undefined || isNaN(seconds)) {
      return '0:00';
    }

    const totalSeconds = Math.floor(Math.abs(seconds));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;

    if (format === 'long') {
      if (hours > 0) {
        const hourText = hours === 1 ? 'ώρα' : 'ώρες';
        const minuteText = minutes === 1 ? 'λεπτό' : 'λεπτά';
        const secondText = secs === 1 ? 'δευτερόλεπτο' : 'δευτερόλεπτα';
        
        if (minutes > 0 && secs > 0) {
          return `${hours} ${hourText}, ${minutes} ${minuteText}, ${secs} ${secondText}`;
        } else if (minutes > 0) {
          return `${hours} ${hourText}, ${minutes} ${minuteText}`;
        } else {
          return `${hours} ${hourText}`;
        }
      } else if (minutes > 0) {
        const minuteText = minutes === 1 ? 'λεπτό' : 'λεπτά';
        const secondText = secs === 1 ? 'δευτερόλεπτο' : 'δευτερόλεπτα';
        
        if (secs > 0) {
          return `${minutes} ${minuteText}, ${secs} ${secondText}`;
        } else {
          return `${minutes} ${minuteText}`;
        }
      } else {
        const secondText = secs === 1 ? 'δευτερόλεπτο' : 'δευτερόλεπτα';
        return `${secs} ${secondText}`;
      }
    }

    // Short format
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }
}