"""
Enhanced WER/CER Calculator for Greek ASR - Optimized Version
Based on international standards and Greek language specifics

This module implements state-of-the-art algorithms for ASR evaluation,
specifically optimized for Greek language with proper handling of:
- Monotonic vs Polytonic orthography
- Greek diacritics (τόνοι)
- Dialectal variations
- Character normalization
"""

import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class GreekOrthography(Enum):
    """Greek orthography types."""
    MONOTONIC = "monotonic"    # Modern Greek (since 1982)
    POLYTONIC = "polytonic"    # Ancient/Traditional Greek
    MIXED = "mixed"            # Both systems present


@dataclass
class NormalizationConfig:
    """Configuration for text normalization."""
    lowercase: bool = True
    remove_punctuation: bool = True
    normalize_diacritics: bool = True
    normalize_numbers: bool = True
    normalize_whitespace: bool = True
    greek_specific: bool = True
    preserve_case_for_proper_nouns: bool = False


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics for ASR."""
    # Core metrics
    wer: float                  # Word Error Rate (%)
    cer: float                  # Character Error Rate (%)
    word_accuracy: float        # 100 - WER
    char_accuracy: float        # 100 - CER
    
    # Detailed error breakdown
    substitutions: int
    deletions: int
    insertions: int
    
    # Greek-specific metrics
    diacritic_accuracy: float   # Accuracy of τόνοι placement
    diacritic_errors: float     # Percentage of diacritic errors
    greek_char_accuracy: float  # Accuracy of Greek characters only
    
    # Additional metrics
    normalized_edit_distance: float  # Edit distance / max(len(ref), len(hyp))
    word_information_preserved: float  # Semantic similarity score
    
    # Metadata
    reference_word_count: int
    hypothesis_word_count: int
    reference_char_count: int
    hypothesis_char_count: int
    orthography_type: str


class GreekTextNormalizer:
    """Advanced text normalizer for Greek ASR evaluation."""
    
    # Greek character ranges
    GREEK_LOWERCASE = '\u03b1-\u03c9'
    GREEK_UPPERCASE = '\u0391-\u03a9'
    GREEK_EXTENDED = '\u1f00-\u1fff'
    
    # Monotonic diacritics (Modern Greek)
    MONOTONIC_ACCENTED = {
        'ά': 'α', 'έ': 'ε', 'ή': 'η', 'ί': 'ι', 
        'ό': 'ο', 'ύ': 'υ', 'ώ': 'ω'
    }
    
    # Polytonic diacritics (Ancient Greek)
    POLYTONIC_MAP = {
        # Oxeia (acute)
        '\u1f71': 'α', '\u1f73': 'ε', '\u1f75': 'η', '\u1f77': 'ι',
        '\u1f79': 'ο', '\u1f7b': 'υ', '\u1f7d': 'ω',
        # Varia (grave)
        '\u1f70': 'α', '\u1f72': 'ε', '\u1f74': 'η', '\u1f76': 'ι',
        '\u1f78': 'ο', '\u1f7a': 'υ', '\u1f7c': 'ω',
        # Perispomeni (circumflex)
        '\u1fb6': 'α', '\u1fc6': 'η', '\u1fd6': 'ι',
        '\u1fe6': 'υ', '\u1ff6': 'ω',
    }
    
    def __init__(self, config: Optional[NormalizationConfig] = None):
        self.config = config or NormalizationConfig()
    
    def detect_orthography(self, text: str) -> GreekOrthography:
        """Detect the orthography system used in the text."""
        has_monotonic = bool(re.search(r'[άέήίόύώΐΰ]', text))
        has_polytonic = bool(re.search(r'[\u1f00-\u1fff]', text))
        
        if has_polytonic and not has_monotonic:
            return GreekOrthography.POLYTONIC
        elif has_monotonic and not has_polytonic:
            return GreekOrthography.MONOTONIC
        elif has_monotonic and has_polytonic:
            return GreekOrthography.MIXED
        else:
            return GreekOrthography.MONOTONIC  # Default
    
    def normalize(self, text: str) -> str:
        """Normalize text according to configuration."""
        if not text:
            return ""
        
        # Unicode normalization (NFC for Greek)
        text = unicodedata.normalize('NFC', text)
        
        # Case normalization
        if self.config.lowercase:
            text = text.lower()
        
        # Greek-specific normalization
        if self.config.greek_specific:
            text = self._normalize_greek_specific(text)
        
        # Remove punctuation
        if self.config.remove_punctuation:
            # Keep Greek letters, spaces, and optionally numbers
            pattern = rf'[^{self.GREEK_LOWERCASE}{self.GREEK_UPPERCASE}{self.GREEK_EXTENDED}\s'
            if self.config.normalize_numbers:
                pattern += r'\d'
            pattern += ']'
            text = re.sub(pattern, ' ', text)
        
        # Normalize whitespace
        if self.config.normalize_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _normalize_greek_specific(self, text: str) -> str:
        """Apply Greek-specific normalizations."""
        # Handle final sigma (ς → σ)
        text = text.replace('ς', 'σ')
        
        # Normalize common variations
        text = text.replace('ΐ', 'ϊ')  # Dialytika with tonos
        text = text.replace('ΰ', 'ϋ')  # Dialytika with tonos
        
        # Optional: Convert polytonic to monotonic
        if self.config.normalize_diacritics:
            for poly, mono in self.POLYTONIC_MAP.items():
                text = text.replace(poly, mono)
        
        return text
    
    def remove_diacritics(self, text: str) -> str:
        """Remove all diacritics from Greek text."""
        # Remove monotonic diacritics
        for accented, plain in self.MONOTONIC_ACCENTED.items():
            text = text.replace(accented, plain)
        
        # Remove polytonic diacritics
        for poly, plain in self.POLYTONIC_MAP.items():
            text = text.replace(poly, plain)
        
        # Remove dialytika
        text = text.replace('ϊ', 'ι').replace('ϋ', 'υ')
        
        return text


class OptimizedLevenshteinCalculator:
    """Optimized Levenshtein distance calculator with detailed operation tracking."""
    
    @staticmethod
    def calculate(s1: List[str], s2: List[str]) -> int:
        """Calculate Levenshtein distance using space-optimized algorithm."""
        if len(s1) < len(s2):
            return OptimizedLevenshteinCalculator.calculate(s2, s1)
        
        if not s2:
            return len(s1)
        
        # Use only two rows for space optimization
        previous_row = list(range(len(s2) + 1))
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Calculate costs
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (0 if c1 == c2 else 1)
                
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def calculate_detailed(s1: List[str], s2: List[str]) -> Dict[str, int]:
        """Calculate Levenshtein distance with detailed operation breakdown."""
        len1, len2 = len(s1), len(s2)
        
        # DP table for distances
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Operation tracking
        ops = [[{'sub': 0, 'del': 0, 'ins': 0} for _ in range(len2 + 1)] 
               for _ in range(len1 + 1)]
        
        # Initialize base cases
        for i in range(len1 + 1):
            dp[i][0] = i
            if i > 0:
                ops[i][0] = {'sub': 0, 'del': i, 'ins': 0}
        
        for j in range(len2 + 1):
            dp[0][j] = j
            if j > 0:
                ops[0][j] = {'sub': 0, 'del': 0, 'ins': j}
        
        # Fill DP table
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                    ops[i][j] = ops[i-1][j-1].copy()
                else:
                    costs = [
                        (dp[i-1][j-1] + 1, 'sub', (i-1, j-1)),
                        (dp[i-1][j] + 1, 'del', (i-1, j)),
                        (dp[i][j-1] + 1, 'ins', (i, j-1))
                    ]
                    
                    min_cost, op_type, prev_pos = min(costs)
                    dp[i][j] = min_cost
                    
                    ops[i][j] = ops[prev_pos[0]][prev_pos[1]].copy()
                    ops[i][j][op_type] += 1
        
        return {
            'distance': dp[len1][len2],
            'substitutions': ops[len1][len2]['sub'],
            'deletions': ops[len1][len2]['del'],
            'insertions': ops[len1][len2]['ins']
        }


class GreekDiacriticAnalyzer:
    """Specialized analyzer for Greek diacritics."""
    
    # All Greek characters that can have diacritics
    DIACRITIC_CHARS = 'άέήίόύώΐΰ'
    BASE_CHARS = 'αεηιουωιυ'
    
    @staticmethod
    def analyze_diacritics(reference: str, hypothesis: str, 
                          normalizer: GreekTextNormalizer) -> Dict[str, float]:
        """
        Analyze diacritic accuracy using advanced alignment.
        
        Returns:
            Dictionary with diacritic metrics
        """
        # Normalize texts for comparison
        ref_norm = normalizer.normalize(reference)
        hyp_norm = normalizer.normalize(hypothesis)
        
        # Split into words
        ref_words = ref_norm.split()
        hyp_words = hyp_norm.split()
        
        # Perform word alignment using Levenshtein
        alignment = GreekDiacriticAnalyzer._align_words(ref_words, hyp_words)
        
        total_diacritics = 0
        correct_diacritics = 0
        missed_diacritics = 0
        extra_diacritics = 0
        
        for ref_idx, hyp_idx in alignment:
            if ref_idx is None or hyp_idx is None:
                # Handle insertions/deletions
                if ref_idx is not None:
                    ref_word = ref_words[ref_idx]
                    total_diacritics += sum(1 for c in ref_word if c in GreekDiacriticAnalyzer.DIACRITIC_CHARS)
                continue
            
            ref_word = ref_words[ref_idx]
            hyp_word = hyp_words[hyp_idx]
            
            # Character-level diacritic comparison
            ref_base = normalizer.remove_diacritics(ref_word)
            hyp_base = normalizer.remove_diacritics(hyp_word)
            
            if ref_base == hyp_base:
                # Same base word - check diacritics
                for i, (r_char, h_char) in enumerate(zip(ref_word, hyp_word)):
                    if r_char in GreekDiacriticAnalyzer.DIACRITIC_CHARS:
                        total_diacritics += 1
                        if r_char == h_char:
                            correct_diacritics += 1
                        else:
                            missed_diacritics += 1
                    elif h_char in GreekDiacriticAnalyzer.DIACRITIC_CHARS:
                        extra_diacritics += 1
            else:
                # Different base words - count all ref diacritics as missed
                total_diacritics += sum(1 for c in ref_word if c in GreekDiacriticAnalyzer.DIACRITIC_CHARS)
        
        accuracy = (correct_diacritics / total_diacritics * 100) if total_diacritics > 0 else 100.0
        
        return {
            'accuracy': accuracy,
            'total_diacritics': total_diacritics,
            'correct_diacritics': correct_diacritics,
            'missed_diacritics': missed_diacritics,
            'extra_diacritics': extra_diacritics,
            'precision': (correct_diacritics / (correct_diacritics + extra_diacritics) * 100) 
                        if (correct_diacritics + extra_diacritics) > 0 else 100.0,
            'recall': accuracy  # Same as accuracy in this context
        }
    
    @staticmethod
    def _align_words(ref_words: List[str], hyp_words: List[str]) -> List[Tuple[Optional[int], Optional[int]]]:
        """Align words using minimum edit distance."""
        # Simple alignment based on Levenshtein
        # For production, consider using more sophisticated alignment algorithms
        alignment = []
        
        # Use dynamic programming for alignment
        n, m = len(ref_words), len(hyp_words)
        dp = [[float('inf')] * (m + 1) for _ in range(n + 1)]
        
        # Initialize
        dp[0][0] = 0
        for i in range(1, n + 1):
            dp[i][0] = i
        for j in range(1, m + 1):
            dp[0][j] = j
        
        # Fill DP table
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if ref_words[i-1] == hyp_words[j-1] else 1
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + cost  # substitution
                )
        
        # Backtrack to find alignment
        i, j = n, m
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (0 if ref_words[i-1] == hyp_words[j-1] else 1):
                alignment.append((i-1, j-1))
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                alignment.append((i-1, None))
                i -= 1
            else:
                alignment.append((None, j-1))
                j -= 1
        
        return list(reversed(alignment))


class GreekASRCalculator:
    """Main calculator for Greek ASR evaluation metrics."""
    
    def __init__(self, config: Optional[NormalizationConfig] = None):
        self.normalizer = GreekTextNormalizer(config)
        self.levenshtein = OptimizedLevenshteinCalculator()
        self.diacritic_analyzer = GreekDiacriticAnalyzer()
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        Calculate Word Error Rate (WER) according to NIST standards.
        
        WER = (S + D + I) / N × 100
        where S = substitutions, D = deletions, I = insertions, N = reference words
        """
        if not reference:
            return 100.0 if hypothesis else 0.0
        
        if not hypothesis:
            return 100.0
        
        # Normalize texts
        ref_norm = self.normalizer.normalize(reference)
        hyp_norm = self.normalizer.normalize(hypothesis)
        
        # Split into words
        ref_words = ref_norm.split()
        hyp_words = hyp_norm.split()
        
        if not ref_words:
            return 0.0 if not hyp_words else 100.0
        
        # Calculate edit distance
        distance = self.levenshtein.calculate(ref_words, hyp_words)
        
        # Calculate WER
        wer = (distance / len(ref_words)) * 100
        
        # Ensure WER is within [0, 100] for practical purposes
        # Note: WER can theoretically exceed 100% if hypothesis has many insertions
        return min(wer, 200.0)  # Cap at 200% for extreme cases
    
    def calculate_cer(self, reference: str, hypothesis: str) -> float:
        """
        Calculate Character Error Rate (CER).
        
        CER = (S + D + I) / N × 100
        where operations are at character level
        """
        if not reference:
            return 100.0 if hypothesis else 0.0
        
        if not hypothesis:
            return 100.0
        
        # Normalize texts
        ref_norm = self.normalizer.normalize(reference)
        hyp_norm = self.normalizer.normalize(hypothesis)
        
        # Remove spaces for character-level comparison
        ref_chars = list(ref_norm.replace(' ', ''))
        hyp_chars = list(hyp_norm.replace(' ', ''))
        
        if not ref_chars:
            return 0.0 if not hyp_chars else 100.0
        
        # Calculate edit distance
        distance = self.levenshtein.calculate(ref_chars, hyp_chars)
        
        # Calculate CER
        cer = (distance / len(ref_chars)) * 100
        
        return min(cer, 200.0)  # Cap at 200%
    
    def calculate_detailed_metrics(self, reference: str, hypothesis: str) -> EvaluationMetrics:
        """Calculate comprehensive evaluation metrics."""
        # Basic WER/CER
        wer = self.calculate_wer(reference, hypothesis)
        cer = self.calculate_cer(reference, hypothesis)
        
        # Normalized texts
        ref_norm = self.normalizer.normalize(reference)
        hyp_norm = self.normalizer.normalize(hypothesis)
        
        # Word and character counts
        ref_words = ref_norm.split()
        hyp_words = hyp_norm.split()
        ref_chars = ref_norm.replace(' ', '')
        hyp_chars = hyp_norm.replace(' ', '')
        
        # Detailed error analysis
        word_details = self.levenshtein.calculate_detailed(ref_words, hyp_words)
        
        # Diacritic analysis
        diacritic_results = self.diacritic_analyzer.analyze_diacritics(
            reference, hypothesis, self.normalizer
        )
        
        # Greek character accuracy
        greek_char_accuracy = self._calculate_greek_char_accuracy(ref_norm, hyp_norm)
        
        # Normalized edit distance
        max_len = max(len(ref_words), len(hyp_words))
        normalized_distance = (word_details['distance'] / max_len * 100) if max_len > 0 else 0.0
        
        # Detect orthography
        orthography = self.normalizer.detect_orthography(reference)
        
        return EvaluationMetrics(
            wer=round(wer, 2),
            cer=round(cer, 2),
            word_accuracy=round(100 - wer, 2),
            char_accuracy=round(100 - cer, 2),
            substitutions=word_details['substitutions'],
            deletions=word_details['deletions'],
            insertions=word_details['insertions'],
            diacritic_accuracy=round(diacritic_results['accuracy'], 2),
            diacritic_errors=round(100 - diacritic_results['accuracy'], 2),
            greek_char_accuracy=round(greek_char_accuracy, 2),
            normalized_edit_distance=round(normalized_distance, 2),
            word_information_preserved=round(100 - normalized_distance, 2),
            reference_word_count=len(ref_words),
            hypothesis_word_count=len(hyp_words),
            reference_char_count=len(ref_chars),
            hypothesis_char_count=len(hyp_chars),
            orthography_type=orthography.value
        )
    
    def _calculate_greek_char_accuracy(self, ref_norm: str, hyp_norm: str) -> float:
        """Calculate accuracy for Greek characters only."""
        # Extract only Greek characters
        greek_pattern = rf'[{self.normalizer.GREEK_LOWERCASE}{self.normalizer.GREEK_UPPERCASE}{self.normalizer.GREEK_EXTENDED}]'
        
        ref_greek = ''.join(re.findall(greek_pattern, ref_norm))
        hyp_greek = ''.join(re.findall(greek_pattern, hyp_norm))
        
        if not ref_greek:
            return 100.0 if not hyp_greek else 0.0
        
        # Calculate character-level accuracy
        distance = self.levenshtein.calculate(list(ref_greek), list(hyp_greek))
        accuracy = max(0.0, 100.0 - (distance / len(ref_greek) * 100))
        
        return accuracy


# Convenience functions for backward compatibility
def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate WER using default configuration."""
    calculator = GreekASRCalculator()
    return calculator.calculate_wer(reference, hypothesis)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculate CER using default configuration."""
    calculator = GreekASRCalculator()
    return calculator.calculate_cer(reference, hypothesis)


def calculate_detailed_metrics(reference: str, hypothesis: str) -> Dict[str, Any]:
    """Calculate detailed metrics using default configuration."""
    calculator = GreekASRCalculator()
    metrics = calculator.calculate_detailed_metrics(reference, hypothesis)
    
    # Convert to dictionary for compatibility
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
        'normalized_edit_distance': metrics.normalized_edit_distance,
        'word_information_preserved': metrics.word_information_preserved,
        'orthography_type': metrics.orthography_type
    }


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            'reference': "πως αν δεν βρω τρόπο να χώσω τον κακομοιρίδη στη φυλακή",
            'hypothesis': "Πως αν δεν βρω τρόπο να χώσω τον Κακομυρίδη στη φυλακή.",
            'description': "Original problematic case"
        },
        {
            'reference': "Καλησπέρα, πώς είστε σήμερα;",
            'hypothesis': "Καλησπέρα, πως είστε σήμερα;",
            'description': "Missing diacritic on πώς"
        },
        {
            'reference': "Το παιδί έπαιζε στην αυλή",
            'hypothesis': "Το παιδι επαιζε στην αυλη",
            'description': "Multiple missing diacritics"
        }
    ]
    
    calculator = GreekASRCalculator()
    
    for i, test in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test Case {i+1}: {test['description']}")
        print(f"Reference:  {test['reference']}")
        print(f"Hypothesis: {test['hypothesis']}")
        print('-'*60)
        
        metrics = calculator.calculate_detailed_metrics(
            test['reference'], 
            test['hypothesis']
        )
        
        print(f"WER: {metrics.wer}% | CER: {metrics.cer}%")
        print(f"Word Accuracy: {metrics.word_accuracy}% | Char Accuracy: {metrics.char_accuracy}%")
        print(f"Operations: S={metrics.substitutions}, D={metrics.deletions}, I={metrics.insertions}")
        print(f"Diacritic Accuracy: {metrics.diacritic_accuracy}%")
        print(f"Greek Char Accuracy: {metrics.greek_char_accuracy}%")
        print(f"Orthography: {metrics.orthography_type}")