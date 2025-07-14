/**
 * WER Result interfaces - Data structures only (NO CALCULATIONS)
 * All calculations are done in the backend
 */

export interface WERResult {
  wer: number;           // Word Error Rate (0.0 - 1.0)
  cer: number;           // Character Error Rate (0.0 - 1.0)
  werPercentage: number; // WER as percentage (0 - 100)
  cerPercentage: number; // CER as percentage (0 - 100)
  
  // Word-level metrics
  wordCount: number;
  substitutions: number;
  deletions: number;
  insertions: number;
  correctWords: number;
  
  // Character-level metrics
  characterCount: number;
  charSubstitutions: number;
  charDeletions: number;
  charInsertions: number;
  correctCharacters: number;
  
  // Additional insights
  accuracy: number;      // 1 - WER (word accuracy)
  charAccuracy: number;  // 1 - CER (character accuracy)
  
  // Greek-specific metrics
  greekCharacterCount: number;
  greekCharacterAccuracy: number;
  diacriticErrors: number;
  diacriticAccuracy: number;
}

export interface ComparisonWERResult {
  whisperWER: WERResult;
  wav2vecWER: WERResult;
  betterModel: 'whisper' | 'wav2vec2';
  werDifference: number;
  cerDifference: number;
  accuracyDifference: number;
}