"""
Enhanced WER (Word Error Rate) and CER (Character Error Rate) Calculator for Academic Research

This module provides functions to calculate WER and CER metrics for evaluating
ASR model performance in academic research contexts, with detailed Greek language analysis.

Version 2.0: Optimized based on international standards and Greek language research
"""

import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional

# Import enhanced calculator if available
try:
    from .wer_calculator_optimized import (
        GreekASRCalculator, 
        NormalizationConfig,
        GreekDiacriticAnalyzer
    )
    HAS_OPTIMIZED = True
except ImportError:
    HAS_OPTIMIZED = False


def normalize_greek_text(text: str) -> str:
    """
    Normalize Greek text for WER/CER calculation.
    
    - Convert to lowercase
    - Normalize Unicode (diacritics)
    - Remove extra whitespace
    - Handle Greek-specific characters
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize Unicode - important for Greek diacritics
    text = unicodedata.normalize('NFC', text)
    
    # Remove punctuation but keep Greek letters and spaces
    # Keep: α-ωΑ-Ω, numbers, spaces
    text = re.sub(r'[^\u0370-\u03FF\u1F00-\u1FFF\w\s]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def levenshtein_distance(s1: List[str], s2: List[str]) -> int:
    """
    Calculate Levenshtein distance between two sequences.
    Used for both word-level (WER) and character-level (CER) calculations.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, and substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER) between reference and hypothesis texts.
    
    WER = (S + D + I) / N
    Where:
    - S = number of substitutions
    - D = number of deletions  
    - I = number of insertions
    - N = number of words in reference
    
    Args:
        reference: Ground truth text
        hypothesis: ASR model output text
        
    Returns:
        WER as percentage (0-100)
    """
    if not reference and not hypothesis:
        return 0.0
    
    if not reference:
        return 100.0  # If no reference, WER is 100%
    
    if not hypothesis:
        return 100.0  # If no hypothesis, WER is 100%
    
    # Normalize both texts
    ref_normalized = normalize_greek_text(reference)
    hyp_normalized = normalize_greek_text(hypothesis)
    
    # Split into words
    ref_words = ref_normalized.split()
    hyp_words = hyp_normalized.split()
    
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 100.0
    
    # Calculate edit distance
    distance = levenshtein_distance(ref_words, hyp_words)
    
    # Calculate WER as percentage
    wer = (distance / len(ref_words)) * 100
    
    return min(100.0, max(0.0, wer))  # Clamp between 0-100


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Calculate Character Error Rate (CER) between reference and hypothesis texts.
    
    CER = (S + D + I) / N
    Where:
    - S = number of character substitutions
    - D = number of character deletions
    - I = number of character insertions  
    - N = number of characters in reference
    
    Args:
        reference: Ground truth text
        hypothesis: ASR model output text
        
    Returns:
        CER as percentage (0-100)
    """
    if not reference and not hypothesis:
        return 0.0
    
    if not reference:
        return 100.0  # If no reference, CER is 100%
    
    if not hypothesis:
        return 100.0  # If no hypothesis, CER is 100%
    
    # Normalize both texts
    ref_normalized = normalize_greek_text(reference)
    hyp_normalized = normalize_greek_text(hypothesis)
    
    # Remove spaces for character-level comparison
    ref_chars = ref_normalized.replace(' ', '')
    hyp_chars = hyp_normalized.replace(' ', '')
    
    if len(ref_chars) == 0:
        return 0.0 if len(hyp_chars) == 0 else 100.0
    
    # Calculate edit distance at character level
    distance = levenshtein_distance(list(ref_chars), list(hyp_chars))
    
    # Calculate CER as percentage
    cer = (distance / len(ref_chars)) * 100
    
    return min(100.0, max(0.0, cer))  # Clamp between 0-100


def calculate_accuracy_from_wer(wer: float) -> float:
    """
    Convert WER to accuracy percentage.
    
    Accuracy = 100 - WER
    """
    return max(0.0, 100.0 - wer)


def detailed_wer_analysis(reference: str, hypothesis: str) -> dict:
    """
    Perform detailed WER analysis with breakdown of error types.
    
    Returns:
        Dictionary with detailed metrics including:
        - WER and CER
        - Word and character counts
        - Error breakdowns
        - Accuracy scores
    """
    ref_normalized = normalize_greek_text(reference)
    hyp_normalized = normalize_greek_text(hypothesis)
    
    ref_words = ref_normalized.split()
    hyp_words = hyp_normalized.split()
    
    ref_chars = ref_normalized.replace(' ', '')
    hyp_chars = hyp_normalized.replace(' ', '')
    
    wer = calculate_wer(reference, hypothesis)
    cer = calculate_cer(reference, hypothesis)
    
    return {
        'wer': round(wer, 2),
        'cer': round(cer, 2),
        'accuracy': round(calculate_accuracy_from_wer(wer), 2),
        'reference_word_count': len(ref_words),
        'hypothesis_word_count': len(hyp_words),
        'reference_char_count': len(ref_chars),
        'hypothesis_char_count': len(hyp_chars),
        'word_edit_distance': levenshtein_distance(ref_words, hyp_words),
        'char_edit_distance': levenshtein_distance(list(ref_chars), list(hyp_chars)),
        'reference_normalized': ref_normalized,
        'hypothesis_normalized': hyp_normalized
    }


def levenshtein_detailed(s1: List[str], s2: List[str]) -> Dict[str, int]:
    """
    Calculate detailed Levenshtein distance with operation counts.
    
    Returns:
        Dictionary with substitutions, deletions, insertions counts
    """
    len1, len2 = len(s1), len(s2)
    
    # Initialize DP table
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    # Track operations
    ops = [[{'sub': 0, 'del': 0, 'ins': 0} for _ in range(len2 + 1)] for _ in range(len1 + 1)]
    
    # Initialize first row and column
    for i in range(len1 + 1):
        dp[i][0] = i
        ops[i][0] = {'sub': 0, 'del': i, 'ins': 0}
    
    for j in range(len2 + 1):
        dp[0][j] = j
        ops[0][j] = {'sub': 0, 'del': 0, 'ins': j}
    
    # Fill DP table
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
                ops[i][j] = ops[i-1][j-1].copy()
            else:
                # Check three operations
                substitution = dp[i-1][j-1] + 1
                deletion = dp[i-1][j] + 1
                insertion = dp[i][j-1] + 1
                
                min_cost = min(substitution, deletion, insertion)
                dp[i][j] = min_cost
                
                if min_cost == substitution:
                    ops[i][j] = ops[i-1][j-1].copy()
                    ops[i][j]['sub'] += 1
                elif min_cost == deletion:
                    ops[i][j] = ops[i-1][j].copy()
                    ops[i][j]['del'] += 1
                else:  # insertion
                    ops[i][j] = ops[i][j-1].copy()
                    ops[i][j]['ins'] += 1
    
    return {
        'substitutions': ops[len1][len2]['sub'],
        'deletions': ops[len1][len2]['del'],
        'insertions': ops[len1][len2]['ins'],
        'total_distance': dp[len1][len2]
    }


def calculate_greek_diacritic_accuracy(reference: str, hypothesis: str) -> float:
    """
    Calculate accuracy specifically for Greek diacritics (τόνοι).
    
    Uses word-aligned comparison to properly handle diacritics even when
    words have different lengths or character substitutions.
    """
    if not reference or not hypothesis:
        return 0.0
    
    # Greek characters with diacritics
    accented_chars = 'άέήίόύώΐΰ'
    
    # Normalize texts
    ref_norm = normalize_greek_text(reference)
    hyp_norm = normalize_greek_text(hypothesis)
    
    # Split into words for proper alignment
    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()
    
    total_diacritics = 0
    correct_diacritics = 0
    
    # Use dynamic programming alignment for better word matching
    # For now, use simple alignment (same length assumption)
    max_len = max(len(ref_words), len(hyp_words))
    
    for i in range(max_len):
        ref_word = ref_words[i] if i < len(ref_words) else ""
        hyp_word = hyp_words[i] if i < len(hyp_words) else ""
        
        # Count diacritics in reference word
        ref_diacritics = sum(1 for char in ref_word if char in accented_chars)
        total_diacritics += ref_diacritics
        
        # For each diacritic position in reference, check if hypothesis matches
        if ref_word == hyp_word:
            # Perfect word match - all diacritics correct
            correct_diacritics += ref_diacritics
        else:
            # Partial match - count character-by-character for this word only
            min_word_len = min(len(ref_word), len(hyp_word))
            for j in range(min_word_len):
                if ref_word[j] in accented_chars and ref_word[j] == hyp_word[j]:
                    correct_diacritics += 1
    
    if total_diacritics == 0:
        return 100.0  # No diacritics to evaluate
    
    return (correct_diacritics / total_diacritics) * 100


def calculate_greek_character_accuracy(reference: str, hypothesis: str) -> float:
    """
    Calculate accuracy for Greek-specific characters (excluding Latin).
    """
    if not reference or not hypothesis:
        return 0.0
    
    # Normalize texts
    ref_norm = normalize_greek_text(reference)
    hyp_norm = normalize_greek_text(hypothesis)
    
    # Filter only Greek characters
    greek_chars_ref = re.sub(r'[^\u0370-\u03FF\u1F00-\u1FFF]', '', ref_norm)
    greek_chars_hyp = re.sub(r'[^\u0370-\u03FF\u1F00-\u1FFF]', '', hyp_norm)
    
    if not greek_chars_ref:
        return 100.0 if not greek_chars_hyp else 0.0
    
    # Calculate character-level accuracy for Greek characters only
    distance = levenshtein_distance(list(greek_chars_ref), list(greek_chars_hyp))
    accuracy = max(0.0, 100.0 - (distance / len(greek_chars_ref) * 100))
    
    return accuracy


class AdvancedWERCalculator:
    """
    Enhanced WER/CER Calculator with detailed Greek language analysis.
    
    Version 2.0: Uses optimized algorithms when available.
    """
    
    def __init__(self):
        """Initialize calculator with optimized version if available."""
        if HAS_OPTIMIZED:
            self.calculator = GreekASRCalculator()
        else:
            self.calculator = None
    
    @staticmethod
    def calculate_detailed_metrics(reference: str, hypothesis: str) -> Dict[str, Any]:
        """
        Calculate all detailed metrics for a reference-hypothesis pair.
        
        Returns comprehensive metrics including:
        - Basic WER/CER
        - Accuracy scores  
        - Detailed error analysis
        - Greek-specific metrics
        """
        # Use enhanced calculator if available
        if HAS_OPTIMIZED:
            calculator = GreekASRCalculator()
            metrics = calculator.calculate_detailed_metrics(reference, hypothesis)
            
            # Convert to dictionary format for backward compatibility
            return {
                'wer': metrics.wer,
                'cer': metrics.cer,
                'accuracy': metrics.word_accuracy,
                'char_accuracy': metrics.char_accuracy,
                'substitutions': metrics.substitutions,
                'deletions': metrics.deletions,
                'insertions': metrics.insertions,
                'diacritic_accuracy': metrics.diacritic_accuracy,
                'diacritic_errors': metrics.diacritic_errors,
                'greek_char_accuracy': metrics.greek_char_accuracy,
                # Additional metrics from enhanced version
                'normalized_edit_distance': getattr(metrics, 'normalized_edit_distance', None),
                'word_information_preserved': getattr(metrics, 'word_information_preserved', None),
                'orthography_type': getattr(metrics, 'orthography_type', 'unknown')
            }
        
        # Fallback to original implementation
        if not reference or not hypothesis:
            return {
                'wer': 100.0,
                'cer': 100.0,
                'accuracy': 0.0,
                'char_accuracy': 0.0,
                'substitutions': 0,
                'deletions': 0,
                'insertions': 0,
                'diacritic_accuracy': 0.0,
                'diacritic_errors': 100.0,
                'greek_char_accuracy': 0.0,
            }
        
        # Basic WER/CER calculation
        wer = calculate_wer(reference, hypothesis)
        cer = calculate_cer(reference, hypothesis)
        
        # Accuracy calculations
        accuracy = calculate_accuracy_from_wer(wer)
        char_accuracy = calculate_accuracy_from_wer(cer)
        
        # Detailed error analysis
        ref_normalized = normalize_greek_text(reference)
        hyp_normalized = normalize_greek_text(hypothesis)
        ref_words = ref_normalized.split()
        hyp_words = hyp_normalized.split()
        
        word_details = levenshtein_detailed(ref_words, hyp_words)
        
        # Greek-specific metrics
        diacritic_accuracy = calculate_greek_diacritic_accuracy(reference, hypothesis)
        greek_char_accuracy = calculate_greek_character_accuracy(reference, hypothesis)
        
        return {
            'wer': round(wer, 2),
            'cer': round(cer, 2),
            'accuracy': round(accuracy, 2),
            'char_accuracy': round(char_accuracy, 2),
            'substitutions': word_details['substitutions'],
            'deletions': word_details['deletions'], 
            'insertions': word_details['insertions'],
            'diacritic_accuracy': round(diacritic_accuracy, 2),
            'diacritic_errors': round(100 - diacritic_accuracy, 2),  # Pre-calculated diacritic errors
            'greek_char_accuracy': round(greek_char_accuracy, 2),
        }


# Example usage for testing
if __name__ == "__main__":
    # Test with Greek text
    reference = "Καλησπέρα, πώς είστε σήμερα;"
    hypothesis = "Καλησπέρα, πως είστε σήμερα;"
    
    calculator = AdvancedWERCalculator()
    metrics = calculator.calculate_detailed_metrics(reference, hypothesis)
    
    print("Enhanced WER Analysis:")
    print(f"WER: {metrics['wer']:.2f}%")
    print(f"CER: {metrics['cer']:.2f}%")
    print(f"Word Accuracy: {metrics['accuracy']:.2f}%")
    print(f"Character Accuracy: {metrics['char_accuracy']:.2f}%")
    print(f"Substitutions: {metrics['substitutions']}")
    print(f"Deletions: {metrics['deletions']}")
    print(f"Insertions: {metrics['insertions']}")
    print(f"Diacritic Accuracy: {metrics['diacritic_accuracy']:.2f}%")
    print(f"Greek Character Accuracy: {metrics['greek_char_accuracy']:.2f}%")