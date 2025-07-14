import { CommonModule } from '@angular/common';
import { Component, Input, inject } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="font-bold text-slate-600 dark:text-white flex items-center"
      [class.cursor-pointer]="isClickable"
      [class.hover:text-cyan-600]="isClickable"
      [class.dark:hover:text-cyan-400]="isClickable"
      [class.transition-colors]="isClickable"
      [class.duration-200]="isClickable"
      [class.hover:scale-105]="isClickable"
      [class.transition-transform]="isClickable"
      (click)="handleClick()"
      [title]="isClickable ? 'Μετάβαση στην αρχική σελίδα' : ''">
      
      <!-- Microphone Icon -->
      <span 
        [class.mr-2]="!iconOnly"
        [class.text-lg]="size === 'sm'"
        [class.text-xl]="size === 'md'"
        [class.text-2xl]="size === 'lg'"
        [class.text-3xl]="size === 'xl'">
        🎙️
      </span>
      
      <!-- Text (hidden when iconOnly is true) -->
      <span 
        *ngIf="!iconOnly"
        class="transition-opacity duration-300"
        [class.text-lg]="size === 'sm'"
        [class.text-xl]="size === 'md'"
        [class.text-2xl]="size === 'lg'"
        [class.text-3xl]="size === 'xl'">
        GreekSTT
      </span>
    </div>
  `,
  styles: []
})
export class LogoComponent {
  private readonly router = inject(Router);

  @Input() size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
  @Input() isClickable = true;
  @Input() navigateTo = '/';
  @Input() iconOnly = false;

  handleClick(): void {
    if (this.isClickable) {
      this.router.navigate([this.navigateTo]);
      // Scroll to top for better UX
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }
}