import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, EventEmitter, Input, OnInit, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ConfirmationService } from 'primeng/api';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DividerModule } from 'primeng/divider';
import { TabViewModule } from 'primeng/tabview';
import { TooltipModule } from 'primeng/tooltip';

import { Transcription, TranscriptionSegment } from '../../../core/models/transcription.model';
import { DurationPipe } from '../../pipes/duration.pipe';

export interface TranscriptionEditData {
  segments: EditableSegment[];
  fullText: string;
  isSegmentMode: boolean;
  hasChanges: boolean;
  changeCount: number;
}

export interface EditableSegment extends TranscriptionSegment {
  originalText: string;
  hasChanged: boolean;
  isDeleted?: boolean;
}

@Component({
  selector: 'app-transcription-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    TabViewModule,
    TooltipModule,
    ConfirmDialogModule,
    DividerModule,
    ChipModule,
    BadgeModule,
    DurationPipe
  ],
  providers: [ConfirmationService],
  template: `
    <div class="transcription-editor">
      <!-- Editor Toolbar -->
      <div class="editor-toolbar">
        <div class="toolbar-left">
          <p-button 
            [icon]="isSegmentMode() ? 'pi pi-align-left' : 'pi pi-list'"
            [label]="isSegmentMode() ? 'Λειτουργία Πλήρους Κειμένου' : 'Λειτουργία Τμημάτων'"
            [outlined]="true"
            size="small"
            (onClick)="toggleMode()">
          </p-button>
          
          <p-divider layout="vertical"></p-divider>
          
          <p-button 
            icon="pi pi-magic"
            label="Αυτόματη Διόρθωση"
            [outlined]="true"
            size="small"
            (onClick)="autoCorrect()"
            [disabled]="isProcessing()"
            pTooltip="Εφαρμογή αυτόματων διορθώσεων για κοινά λάθη">
          </p-button>
          
          <p-button 
            icon="pi pi-undo"
            label="Αναίρεση Όλων"
            [outlined]="true"
            size="small"
            (onClick)="resetAllChanges()"
            [disabled]="!hasChanges()">
          </p-button>
        </div>
        
        <div class="toolbar-right">
          <p-chip [label]="changesSummary()" icon="pi pi-pencil" styleClass="change-indicator"></p-chip>
          
          <p-button 
            icon="pi pi-save"
            label="Αποθήκευση Αλλαγών"
            size="small"
            (onClick)="saveChanges()"
            [disabled]="!hasChanges() || isProcessing()">
          </p-button>
        </div>
      </div>

      <!-- Editor Content -->
      <div class="editor-content">
        @if (isSegmentMode()) {
          <!-- Segment-based editing -->
          <div class="segments-editor">
            <div class="segments-info">
              <span class="text-sm text-color-secondary">
                {{ editableSegments().length }} τμήματα • {{ totalWords() }} λέξεις • {{ totalCharacters() }} χαρακτήρες
              </span>
            </div>
            
            @for (segment of editableSegments(); track segment.start_time; let i = $index) {
              @if (!segment.isDeleted) {
                <div class="segment-editor" 
                     [class.changed]="segment.hasChanged"
                     [class.focused]="focusedSegmentIndex() === i">
                  <div class="segment-header">
                    <div class="segment-info">
                      <span class="segment-number">#{{ i + 1 }}</span>
                      <span class="segment-time">
                        {{ segment.start_time | duration }} - {{ segment.end_time | duration }}
                      </span>
                      @if (segment.hasChanged) {
                        <p-badge value="Τροποποιημένο" severity="warn"></p-badge>
                      }
                    </div>
                    
                    <div class="segment-actions">
                      <p-button 
                        icon="pi pi-play"
                        [rounded]="true"
                        [text]="true"
                        size="small"
                        (onClick)="playSegment(segment)"
                        pTooltip="Αναπαραγωγή τμήματος">
                      </p-button>
                      
                      <p-button 
                        icon="pi pi-undo"
                        [rounded]="true"
                        [text]="true"
                        size="small"
                        (onClick)="resetSegment(segment)"
                        [disabled]="!segment.hasChanged"
                        pTooltip="Αναίρεση αλλαγών">
                      </p-button>
                      
                      <p-button 
                        icon="pi pi-trash"
                        [rounded]="true"
                        [text]="true"
                        size="small"
                        severity="danger"
                        (onClick)="deleteSegment(segment)"
                        pTooltip="Διαγραφή τμήματος">
                      </p-button>
                    </div>
                  </div>
                  
                  <textarea
                    [(ngModel)]="segment.text"
                    (input)="onSegmentTextChange(segment, $event)"
                    (focus)="onSegmentFocus(i)"
                    (blur)="onSegmentBlur()"
                    class="segment-textarea"
                    [rows]="calculateRows(segment.text)"
                    placeholder="Εισάγετε κείμενο τμήματος...">
                  </textarea>
                  
                  @if (segment.confidence !== undefined && segment.confidence < 0.8) {
                    <div class="segment-warning">
                      <i class="pi pi-exclamation-triangle"></i>
                      <span>Χαμηλή εμπιστοσύνη: {{ (segment.confidence * 100).toFixed(0) }}%</span>
                    </div>
                  }
                </div>
              }
            }
            
            @if (deletedSegments().length > 0) {
              <div class="deleted-segments-notice">
                <i class="pi pi-info-circle"></i>
                <span>{{ deletedSegments().length }} διαγραμμένα τμήματα</span>
                <p-button 
                  label="Επαναφορά όλων"
                  size="small"
                  [text]="true"
                  (onClick)="restoreAllDeleted()">
                </p-button>
              </div>
            }
          </div>
        } @else {
          <!-- Full text editing -->
          <div class="text-editor">
            <div class="text-info">
              <span class="text-sm text-color-secondary">
                {{ fullTextWords() }} λέξεις • {{ fullTextCharacters() }} χαρακτήρες
              </span>
              
              @if (hasTextChanges()) {
                <p-badge value="Τροποποιημένο" severity="warn"></p-badge>
              }
            </div>
            
            <textarea
              [(ngModel)]="fullText"
              (input)="onFullTextChange($event)"
              class="full-text-textarea"
              placeholder="Επεξεργαστείτε το πλήρες κείμενο εδώ..."
              [rows]="20">
            </textarea>
            
            <div class="text-editor-help">
              <i class="pi pi-info-circle"></i>
              <span>
                Στη λειτουργία πλήρους κειμένου, οι αλλαγές δεν θα διατηρήσουν τις χρονικές σημάνσεις των τμημάτων.
              </span>
            </div>
          </div>
        }
      </div>

      <!-- Change Summary -->
      @if (hasChanges()) {
        <div class="change-summary">
          <div class="summary-header">
            <h4>Σύνοψη Αλλαγών</h4>
            <p-button 
              label="Προεπισκόπηση"
              icon="pi pi-eye"
              size="small"
              [text]="true"
              (onClick)="showChangePreview()">
            </p-button>
          </div>
          
          <div class="summary-content">
            <div class="summary-item">
              <i class="pi pi-pencil"></i>
              <span>{{ modifiedSegments().length }} τροποποιημένα τμήματα</span>
            </div>
            
            @if (deletedSegments().length > 0) {
              <div class="summary-item">
                <i class="pi pi-trash"></i>
                <span>{{ deletedSegments().length }} διαγραμμένα τμήματα</span>
              </div>
            }
            
            <div class="summary-item">
              <i class="pi pi-align-left"></i>
              <span>{{ absoluteWordCountDiff() }} {{ wordCountDiff() > 0 ? 'προστέθηκαν' : 'αφαιρέθηκαν' }} λέξεις</span>
            </div>
          </div>
        </div>
      }
    </div>

    <!-- confirmDialog provided by app.component.html -->
  `,
  styleUrls: ['./transcription-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TranscriptionEditorComponent implements OnInit {
  @Input() transcription: Transcription | null = null;
  @Output() contentChange = new EventEmitter<TranscriptionEditData>();
  @Output() save = new EventEmitter<TranscriptionEditData>();
  @Output() playSegmentRequest = new EventEmitter<TranscriptionSegment>();

  // Editor state
  readonly isSegmentMode = signal(true);
  readonly editableSegments = signal<EditableSegment[]>([]);
  readonly fullText = signal('');
  readonly originalFullText = signal('');
  readonly isProcessing = signal(false);
  readonly focusedSegmentIndex = signal(-1);

  // Computed values
  readonly hasChanges = computed(() => {
    if (this.isSegmentMode()) {
      return this.editableSegments().some(s => s.hasChanged || s.isDeleted);
    } else {
      return this.fullText() !== this.originalFullText();
    }
  });

  readonly hasTextChanges = computed(() => this.fullText() !== this.originalFullText());

  readonly modifiedSegments = computed(() => 
    this.editableSegments().filter(s => s.hasChanged && !s.isDeleted)
  );

  readonly deletedSegments = computed(() => 
    this.editableSegments().filter(s => s.isDeleted)
  );

  readonly changesSummary = computed(() => {
    const modified = this.modifiedSegments().length;
    const deleted = this.deletedSegments().length;
    const total = modified + deleted;
    
    if (total === 0) return 'Χωρίς αλλαγές';
    if (total === 1) return '1 αλλαγή';
    return `${total} αλλαγές`;
  });

  readonly totalWords = computed(() => {
    const segments = this.editableSegments().filter(s => !s.isDeleted);
    const text = segments.map(s => s.text).join(' ');
    return this.countWords(text);
  });

  readonly totalCharacters = computed(() => {
    const segments = this.editableSegments().filter(s => !s.isDeleted);
    const text = segments.map(s => s.text).join(' ');
    return text.length;
  });

  readonly fullTextWords = computed(() => this.countWords(this.fullText()));
  readonly fullTextCharacters = computed(() => this.fullText().length);

  readonly wordCountDiff = computed(() => {
    if (this.isSegmentMode()) {
      const original = this.countWords(this.editableSegments().map(s => s.originalText).join(' '));
      const current = this.totalWords();
      return current - original;
    } else {
      const original = this.countWords(this.originalFullText());
      const current = this.fullTextWords();
      return current - original;
    }
  });

  readonly absoluteWordCountDiff = computed(() => Math.abs(this.wordCountDiff()));

  constructor(private confirmationService: ConfirmationService) {}

  ngOnInit() {
    this.initializeEditor();
  }

  private initializeEditor(): void {
    if (!this.transcription) return;

    // Initialize segments
    const segments = (this.transcription.segments || []).map(s => ({
      ...s,
      originalText: s.text,
      hasChanged: false,
      isDeleted: false
    }));

    this.editableSegments.set(segments);

    // Initialize full text
    const fullText = this.transcription.text || segments.map(s => s.text).join(' ');
    this.fullText.set(fullText);
    this.originalFullText.set(fullText);
  }

  toggleMode(): void {
    if (this.hasChanges()) {
      this.confirmationService.confirm({
        message: 'Η αλλαγή λειτουργίας θα απορρίψει τις μη αποθηκευμένες αλλαγές. Θέλετε να συνεχίσετε;',
        header: 'Επιβεβαίωση',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.isSegmentMode.update(mode => !mode);
          this.resetAllChanges();
        }
      });
    } else {
      this.isSegmentMode.update(mode => !mode);
    }
  }

  onSegmentTextChange(segment: EditableSegment, event: any): void {
    const newText = event.target.value;
    segment.text = newText;
    segment.hasChanged = segment.text !== segment.originalText;
    this.emitContentChange();
  }

  onFullTextChange(event: any): void {
    this.fullText.set(event.target.value);
    this.emitContentChange();
  }

  onSegmentFocus(index: number): void {
    this.focusedSegmentIndex.set(index);
  }

  onSegmentBlur(): void {
    this.focusedSegmentIndex.set(-1);
  }

  async autoCorrect(): Promise<void> {
    this.isProcessing.set(true);
    
    try {
      // Simulate auto-correction
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (this.isSegmentMode()) {
        const segments = this.editableSegments();
        const corrected = segments.map(segment => {
          if (segment.isDeleted) return segment;
          
          let correctedText = segment.text;
          
          // Basic Greek corrections
          correctedText = correctedText.replace(/\s+/g, ' '); // Multiple spaces
          correctedText = correctedText.replace(/\s+([.,;!?])/g, '$1'); // Space before punctuation
          correctedText = correctedText.replace(/([.,;!?])\s*([α-ωΑ-Ω])/g, '$1 $2'); // Space after punctuation
          correctedText = correctedText.trim();
          
          // Greek-specific corrections
          correctedText = correctedText.replace(/ειναι/g, 'είναι');
          correctedText = correctedText.replace(/εχει/g, 'έχει');
          correctedText = correctedText.replace(/ητανε?/g, 'ήταν');
          
          return {
            ...segment,
            text: correctedText,
            hasChanged: correctedText !== segment.originalText
          };
        });
        
        this.editableSegments.set(corrected);
      } else {
        let correctedText = this.fullText();
        
        // Apply same corrections
        correctedText = correctedText.replace(/\s+/g, ' ');
        correctedText = correctedText.replace(/\s+([.,;!?])/g, '$1');
        correctedText = correctedText.replace(/([.,;!?])\s*([α-ωΑ-Ω])/g, '$1 $2');
        correctedText = correctedText.trim();
        
        correctedText = correctedText.replace(/ειναι/g, 'είναι');
        correctedText = correctedText.replace(/εχει/g, 'έχει');
        correctedText = correctedText.replace(/ητανε?/g, 'ήταν');
        
        this.fullText.set(correctedText);
      }
      
      this.emitContentChange();
    } finally {
      this.isProcessing.set(false);
    }
  }

  resetSegment(segment: EditableSegment): void {
    segment.text = segment.originalText;
    segment.hasChanged = false;
    segment.isDeleted = false;
    this.emitContentChange();
  }

  deleteSegment(segment: EditableSegment): void {
    this.confirmationService.confirm({
      message: 'Είστε βέβαιοι ότι θέλετε να διαγράψετε αυτό το τμήμα;',
      header: 'Επιβεβαίωση Διαγραφής',
      icon: 'pi pi-trash',
      accept: () => {
        segment.isDeleted = true;
        this.emitContentChange();
      }
    });
  }

  restoreAllDeleted(): void {
    const segments = this.editableSegments();
    const restored = segments.map(s => ({ ...s, isDeleted: false }));
    this.editableSegments.set(restored);
    this.emitContentChange();
  }

  resetAllChanges(): void {
    this.confirmationService.confirm({
      message: 'Όλες οι αλλαγές θα χαθούν. Θέλετε να συνεχίσετε;',
      header: 'Επιβεβαίωση Αναίρεσης',
      icon: 'pi pi-undo',
      accept: () => {
        this.initializeEditor();
        this.emitContentChange();
      }
    });
  }

  saveChanges(): void {
    const editData = this.getEditData();
    this.save.emit(editData);
  }

  showChangePreview(): void {
    // Could open a dialog showing before/after comparison
    console.log('Show change preview');
  }

  playSegment(segment: TranscriptionSegment): void {
    this.playSegmentRequest.emit(segment);
  }

  calculateRows(text: string): number {
    const minRows = 2;
    const lineBreaks = (text.match(/\n/g) || []).length;
    const charRows = Math.ceil(text.length / 80);
    return Math.max(minRows, lineBreaks + 1, charRows);
  }

  private countWords(text: string): number {
    return text ? text.trim().split(/\s+/).filter(word => word.length > 0).length : 0;
  }

  private emitContentChange(): void {
    const editData = this.getEditData();
    this.contentChange.emit(editData);
  }

  private getEditData(): TranscriptionEditData {
    return {
      segments: this.editableSegments(),
      fullText: this.fullText(),
      isSegmentMode: this.isSegmentMode(),
      hasChanges: this.hasChanges(),
      changeCount: this.modifiedSegments().length + this.deletedSegments().length
    };
  }
}