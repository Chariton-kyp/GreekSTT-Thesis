import { CommonModule } from '@angular/common';
import { Component, Input, Output, EventEmitter, forwardRef, OnInit } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-code-input',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex space-x-3 justify-center">
      <input
        *ngFor="let digit of digits; let i = index"
        #digitInput
        type="text"
        maxlength="1"
        [value]="digit"
        (input)="onDigitInput($event, i)"
        (keydown)="onKeyDown($event, i)"
        (focus)="onDigitFocus(i)"
        (blur)="onBlur()"
        [disabled]="disabled"
        class="w-12 h-12 text-center text-xl font-semibold border-2 rounded-lg focus:border-cyan-500 focus:outline-none text-gray-900 dark:text-white bg-white dark:bg-gray-700 transition-colors"
        [class.border-red-500]="hasError"
        [class.dark:border-red-400]="hasError"
        [class.border-gray-300]="!hasError && !focused"
        [class.dark:border-gray-600]="!hasError && !focused"
        [class.border-cyan-500]="!hasError && focused"
        [class.dark:border-cyan-400]="!hasError && focused"
      />
    </div>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CodeInputComponent),
      multi: true
    }
  ]
})
export class CodeInputComponent implements OnInit, ControlValueAccessor {
  @Input() length: number = 6;
  @Input() disabled: boolean = false;
  @Input() errorMessage: string = '';
  @Input() expiresIn: number = 0;
  @Input() showResend: boolean = false;
  @Input() resendCooldown: number = 0;
  @Input() autoSubmit: boolean = false;
  @Output() valueChange = new EventEmitter<string>();
  @Output() complete = new EventEmitter<string>();
  @Output() resend = new EventEmitter<void>();

  digits: string[] = [];
  focused: boolean = false;
  hasError: boolean = false;

  private onChange = (value: string) => {};
  private onTouched = () => {};

  constructor() {
    this.initializeDigits();
  }

  ngOnInit() {
    this.initializeDigits();
  }

  private initializeDigits() {
    this.digits = new Array(this.length).fill('');
  }

  onDigitInput(event: Event, index: number): void {
    const target = event.target as HTMLInputElement;
    const value = target.value.replace(/[^0-9]/g, '');
    
    if (value.length > 1) {
      // Handle paste or multiple digits
      this.handlePaste(value, index);
      return;
    }

    this.digits[index] = value;
    this.updateValue();

    if (value && index < this.length - 1) {
      this.focusNextInput(index + 1);
    }
  }

  onKeyDown(event: KeyboardEvent, index: number): void {
    const target = event.target as HTMLInputElement;

    if (event.key === 'Backspace') {
      if (!this.digits[index] && index > 0) {
        this.focusPreviousInput(index - 1);
        this.digits[index - 1] = '';
        this.updateValue();
      } else {
        this.digits[index] = '';
        this.updateValue();
      }
    } else if (event.key === 'ArrowLeft' && index > 0) {
      this.focusPreviousInput(index - 1);
    } else if (event.key === 'ArrowRight' && index < this.length - 1) {
      this.focusNextInput(index + 1);
    }
  }

  onDigitFocus(index: number): void {
    this.focused = true;
    this.onTouched();
  }

  onBlur(): void {
    this.focused = false;
  }

  private handlePaste(value: string, startIndex: number): void {
    const digits = value.slice(0, this.length - startIndex).split('');
    
    for (let i = 0; i < digits.length && startIndex + i < this.length; i++) {
      this.digits[startIndex + i] = digits[i];
    }
    
    this.updateValue();
    
    const nextIndex = Math.min(startIndex + digits.length, this.length - 1);
    this.focusNextInput(nextIndex);
  }

  private focusNextInput(index: number): void {
    setTimeout(() => {
      const inputs = document.querySelectorAll('app-code-input input');
      const input = inputs[index] as HTMLInputElement;
      if (input) {
        input.focus();
        input.select();
      }
    }, 0);
  }

  private focusPreviousInput(index: number): void {
    setTimeout(() => {
      const inputs = document.querySelectorAll('app-code-input input');
      const input = inputs[index] as HTMLInputElement;
      if (input) {
        input.focus();
        input.select();
      }
    }, 0);
  }

  private updateValue(): void {
    const value = this.digits.join('');
    this.valueChange.emit(value);
    this.onChange(value);

    if (value.length === this.length) {
      this.complete.emit(value);
    }
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    if (value) {
      const digits = value.slice(0, this.length).split('');
      for (let i = 0; i < this.length; i++) {
        this.digits[i] = digits[i] || '';
      }
    } else {
      this.initializeDigits();
    }
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  // Public methods
  clear(): void {
    this.initializeDigits();
    this.updateValue();
  }

  clearError(): void {
    this.hasError = false;
  }

  setError(): void {
    this.hasError = true;
  }

  focus(): void {
    this.focusNextInput(0);
  }

  showError(message: string): void {
    this.errorMessage = message;
    this.hasError = true;
  }

  updateResendCooldown(cooldown: number): void {
    this.resendCooldown = cooldown;
  }
}