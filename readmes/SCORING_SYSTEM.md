# Fuzzy Matching Score System Documentation

## Table of Contents
1. [Overview](#overview)
2. [API Scoring System](#api-scoring-system)
3. [Local Scoring System](#local-scoring-system)
4. [Combined Scoring Formula](#combined-scoring-formula)
5. [Algorithm Weights](#algorithm-weights)
6. [Match Quality Thresholds](#match-quality-thresholds)
7. [Worked Examples](#worked-examples)
8. [Configuration](#configuration)

---

## Overview

The sanctions screening system uses a **hybrid scoring approach** that combines:
1. **API Score** (60%): From USA Trade API's fuzzy matching algorithm
2. **Local Score** (40%): From 5 local fuzzy matching algorithms

This hybrid approach provides:
- **Finer granularity**: Move from 3 discrete levels (80/90/100) to continuous scale (0-100)
- **False positive reduction**: Local algorithms can identify poor matches that the API rates too highly
- **Transparency**: Users see detailed breakdown of why entities matched
- **Tunability**: Weights and thresholds can be adjusted based on feedback

---

## API Scoring System

### How the USA Trade API Generates Scores

The USA Trade API uses **Microsoft Azure Cognitive Search** with token-based fuzzy matching.

### Score Levels
The API returns three discrete scores:
- **Score 100**: Exact match
- **Score 90**: Close match with minor edits
- **Score 80**: Match with more edits

### Scoring Logic

**Score 100 (Exact Match)**:
- Each valid token in the query has an **exact match** in the result's `name` or `alt_names` field
- Example: Query "Huawei Technologies" → Result "Huawei Technologies Co Ltd"
  - Both tokens ["Huawei", "Technologies"] have exact matches
  - Additional tokens in result (Co, Ltd) don't affect score

**Score 90 (Close Fuzzy Match)**:
- One or more query tokens match with **minimal edits** (1-2 operations)
- Example: Query "Huawei" → Result "Huawai" (1 substitution: e→a)

**Score 80 (Moderate Fuzzy Match)**:
- One or more query tokens match with **more edits** (3+ operations)
- Edit operations include:
  - **Insertions**: Adding characters (e.g., "chris" → "khris")
  - **Deletions**: Removing characters (e.g., "khris" → "kris")
  - **Substitutions**: Replacing characters (e.g., "huawei" → "hawaii")
  - **Transpositions**: Swapping adjacent characters (e.g., "huawei" → "huawiei")

### Key Points
- Query is **tokenized by whitespace**: "Huawei Technologies" → ["Huawei", "Technologies"]
- Score correlates with **number of edits** needed to match
- Checks both primary `name` and `alt_names` fields
- Does not provide edit distance or explain which tokens matched

### API Limitations
1. **Reduced granularity**: Only 3 score levels (old API had 6)
2. **No sub-level scoring**: All "moderate fuzzy matches" get 80, regardless of quality
3. **No explanation**: Doesn't return which tokens matched or per-token edit distance
4. **False positives**: Similar-sounding names get score 80 (e.g., "Huawei" vs "Hawaii Trading")

---

## Local Scoring System

The local scoring system uses **5 different fuzzy matching algorithms** to calculate similarity between the query name and result name.

### Algorithm 1: Token Set Ratio (30% weight)

**Purpose**: Handle company name variations with different word order or legal suffixes

**How it works**:
1. Tokenize both strings by whitespace
2. Compare unique tokens, ignoring duplicates and extra words
3. Returns similarity ratio 0-100

**Example**:
```python
query = "Huawei Technologies"
result = "Huawei Technologies Co Ltd"

# Tokens:
query_tokens = {"huawei", "technologies"}
result_tokens = {"huawei", "technologies", "co", "ltd"}

# Intersection: {"huawei", "technologies"}
# The extra tokens ("co", "ltd") are ignored
# Score: 97 (very high because all query tokens match)
```

**Best for**:
- Company names with legal suffixes (Inc, Ltd, Co, Corp)
- Word order variations
- Extra descriptive words in result

---

### Algorithm 2: Jaro-Winkler Distance (25% weight)

**Purpose**: Optimized for name matching, gives extra weight to matching prefixes

**How it works**:
1. Calculates character-level similarity
2. **Bonus**: Gives higher score if strings match at the beginning
3. Returns similarity ratio 0-100

**Example**:
```python
query = "Huawei"
result = "Huawai"

# Character comparison with transposition consideration
# Prefix "Hua" matches → bonus applied
# Score: 96 (high due to matching prefix and minimal difference)
```

**Best for**:
- Person names and company names
- Typos and minor spelling variations
- Situations where prefix matching is important

---

### Algorithm 3: Levenshtein Distance (20% weight)

**Purpose**: Classic edit distance calculation

**How it works**:
1. Counts minimum number of single-character edits needed to transform one string to another
2. Edits: insertions, deletions, substitutions
3. Normalized to 0-100 scale

**Example**:
```python
query = "Huawei"
result = "Huawai"

# Edit operations needed:
# 1. Substitute 'e' with 'a' at position 4
# Edit distance: 1
# Score: 92 (high similarity, only 1 edit needed)
```

**Best for**:
- Detecting typos
- Character-level similarity
- Baseline similarity measurement

---

### Algorithm 4: Token Sort Ratio (15% weight)

**Purpose**: Handle word order variations by sorting tokens alphabetically

**How it works**:
1. Tokenize both strings
2. Sort tokens alphabetically
3. Compare sorted strings
4. Returns similarity ratio 0-100

**Example**:
```python
query = "Apple Inc"
result = "Inc Apple"

# After sorting:
query_sorted = "apple inc"
result_sorted = "apple inc"

# Score: 100 (perfect match after sorting)
```

**Best for**:
- "First Last" vs "Last, First" name variations
- Company names with reordered words
- Eliminating false negatives from word order

---

### Algorithm 5: Phonetic Matching (10% weight)

**Purpose**: Match names that sound similar but are spelled differently

**How it works**:
1. Converts strings to phonetic codes using Double Metaphone algorithm
2. Compares phonetic codes
3. Returns 100 if codes match, 0 if they don't (binary)

**Example**:
```python
query = "Smith"
result = "Smyth"

# Phonetic codes:
query_code = "SM0"
result_code = "SM0"

# Score: 100 (same pronunciation)
```

**Best for**:
- International names with transliteration issues
- Chinese/Arabic names translated to English differently
- Spelling variations based on pronunciation

---

## Combined Scoring Formula

### Formula

```
combined_score = (api_score × 0.60) + (local_score × 0.40)
```

Where:
- **api_score**: Score from USA Trade API (80, 90, or 100)
- **local_score**: Weighted average of 5 local algorithms (0-100)

### Local Score Calculation

```
local_score = (token_set × 0.30) +
              (jaro_winkler × 0.25) +
              (levenshtein × 0.20) +
              (token_sort × 0.15) +
              (phonetic × 0.10)
```

### Why 60/40 API/Local Split?

1. **API is authoritative**: The API determines which entities are actually in the sanctions database
2. **API is already smart**: Uses token-based matching + edit distance + alt_names checking
3. **Local adds granularity**: Provides finer differentiation within each API tier (80/90/100)
4. **False positive mitigation**: Local scores can downgrade poor API matches
5. **Preserves API signal**: 60% weight ensures API's judgment remains dominant

---

## Algorithm Weights

### Weight Distribution

| Algorithm | Weight | Rationale |
|-----------|--------|-----------|
| Token Set Ratio | 30% | Most important for company names with legal suffixes and word variations |
| Jaro-Winkler | 25% | Excellent for name matching, handles typos and gives prefix bonus |
| Levenshtein | 20% | Baseline edit distance, reliable similarity measure |
| Token Sort | 15% | Handles word order, complements Token Set |
| Phonetic | 10% | Specialized use case (transliteration), binary output limits usefulness |

### Why These Weights?

**Token Set gets highest weight (30%)**:
- Company names often have variations: "Apple Inc", "Apple Incorporated", "Apple Computer Inc"
- Legal suffixes should be ignored: "Co", "Ltd", "Corp", "LLC"
- Most false positives have different token sets: "Huawei" vs "Hawaii Trading Company"

**Jaro-Winkler gets high weight (25%)**:
- Optimized specifically for names
- Prefix matching bonus aligns with how humans match names
- Handles typos naturally

**Levenshtein gets moderate weight (20%)**:
- Reliable baseline measure
- Well-understood algorithm
- Good for detecting character-level differences

**Token Sort gets lower weight (15%)**:
- Less common issue in sanctions lists (names usually in standard format)
- Somewhat redundant with Token Set

**Phonetic gets lowest weight (10%)**:
- Very specialized use case
- Binary output (0 or 100) provides less granularity
- Can create false positives (different words with same pronunciation)

---

## Match Quality Thresholds

### Threshold Levels

| Combined Score | Match Quality | Color | Meaning |
|----------------|---------------|-------|---------|
| ≥ 92 | EXACT | Green | High confidence match, treat as exact |
| 80-91 | HIGH | Blue | Strong fuzzy match, likely correct entity |
| 65-79 | MEDIUM | Yellow | Moderate match, requires investigation |
| < 65 | LOW | Gray | Weak match, likely false positive |

### Rationale

**EXACT (≥ 92)**:
- Includes API score 100 with reasonable local scores
- Includes API score 90 with excellent local scores
- Examples: True exact matches, minor typos in exact names

**HIGH (80-91)**:
- Includes API score 90 with good local scores
- Includes API score 80 with excellent local scores
- Examples: Close variations, legal suffix differences

**MEDIUM (65-79)**:
- Includes API score 80 with moderate local scores
- Examples: Partial matches, similar but not identical entities

**LOW (< 65)**:
- Includes API score 80 with poor local scores
- Examples: False positives like "Huawei" vs "Hawaii Trading"

---

## Worked Examples

### Example 1: Perfect Exact Match

**Input**:
- Query: `"Huawei"`
- Result: `"Huawei"`

**API Score**: 100 (all tokens exact match)

**Local Scores**:
- Token Set Ratio: 100 (identical tokens)
- Jaro-Winkler: 100 (identical strings)
- Levenshtein: 100 (0 edits needed)
- Token Sort: 100 (identical after sorting)
- Phonetic: 100 (same pronunciation)

**Local Score Calculation**:
```
local_score = (100×0.30) + (100×0.25) + (100×0.20) + (100×0.15) + (100×0.10)
            = 30 + 25 + 20 + 15 + 10
            = 100
```

**Combined Score**:
```
combined_score = (100 × 0.60) + (100 × 0.40)
               = 60 + 40
               = 100
```

**Match Quality**: **EXACT** ✅

---

### Example 2: Exact Match with Legal Suffix

**Input**:
- Query: `"Huawei Technologies"`
- Result: `"Huawei Technologies Co Ltd"`

**API Score**: 100 (all query tokens exact match)

**Local Scores**:
- Token Set Ratio: 97 (ignores extra "Co Ltd" tokens, focuses on shared tokens)
- Jaro-Winkler: 94 (extra characters reduce score slightly)
- Levenshtein: 88 (extra characters = more edits)
- Token Sort: 96 (alphabetically sorted comparison)
- Phonetic: 92 (similar pronunciation with extra words)

**Local Score Calculation**:
```
local_score = (97×0.30) + (94×0.25) + (88×0.20) + (96×0.15) + (92×0.10)
            = 29.1 + 23.5 + 17.6 + 14.4 + 9.2
            = 93.8
```

**Combined Score**:
```
combined_score = (100 × 0.60) + (93.8 × 0.40)
               = 60 + 37.5
               = 97.5
```

**Match Quality**: **EXACT** ✅

---

### Example 3: Close Fuzzy Match (Minor Typo)

**Input**:
- Query: `"Huawei"`
- Result: `"Huawai"` (typo in database: e→a)

**API Score**: 90 (1 substitution edit)

**Local Scores**:
- Token Set Ratio: 95 (single token, minor difference)
- Jaro-Winkler: 96 (high due to prefix match "Huaw")
- Levenshtein: 92 (1 character substitution)
- Token Sort: 95 (sorting doesn't help, but still very similar)
- Phonetic: 100 (same pronunciation)

**Local Score Calculation**:
```
local_score = (95×0.30) + (96×0.25) + (92×0.20) + (95×0.15) + (100×0.10)
            = 28.5 + 24.0 + 18.4 + 14.25 + 10.0
            = 95.15
```

**Combined Score**:
```
combined_score = (90 × 0.60) + (95.15 × 0.40)
               = 54 + 38.06
               = 92.06
```

**Match Quality**: **EXACT** ✅
(Local algorithms boost close fuzzy match to exact tier)

---

### Example 4: Moderate Fuzzy Match

**Input**:
- Query: `"Huawei Tech"`
- Result: `"Huawei Technologies Limited"`

**API Score**: 90 (both query tokens match with minor edits)

**Local Scores**:
- Token Set Ratio: 87 (partial token match "Tech" ≠ "Technologies")
- Jaro-Winkler: 84 (partial match, longer result)
- Levenshtein: 78 (significant length difference)
- Token Sort: 85 (sorting helps slightly)
- Phonetic: 88 (similar pronunciation)

**Local Score Calculation**:
```
local_score = (87×0.30) + (84×0.25) + (78×0.20) + (85×0.15) + (88×0.10)
            = 26.1 + 21.0 + 15.6 + 12.75 + 8.8
            = 84.25
```

**Combined Score**:
```
combined_score = (90 × 0.60) + (84.25 × 0.40)
               = 54 + 33.7
               = 87.7
```

**Match Quality**: **HIGH** ✅

---

### Example 5: Weak Fuzzy Match

**Input**:
- Query: `"Huawei"`
- Result: `"Huaweii Corporation"` (extra 'i', different company)

**API Score**: 80 (multiple edits needed)

**Local Scores**:
- Token Set Ratio: 82 (different second token "Corporation")
- Jaro-Winkler: 78 (extra character reduces score)
- Levenshtein: 75 (extra 'i' and " Corporation")
- Token Sort: 80 (sorting doesn't help much)
- Phonetic: 85 (similar pronunciation)

**Local Score Calculation**:
```
local_score = (82×0.30) + (78×0.25) + (75×0.20) + (80×0.15) + (85×0.10)
            = 24.6 + 19.5 + 15.0 + 12.0 + 8.5
            = 79.6
```

**Combined Score**:
```
combined_score = (80 × 0.60) + (79.6 × 0.40)
               = 48 + 31.84
               = 79.84
```

**Match Quality**: **MEDIUM** ⚠️

---

### Example 6: False Positive Caught by Local

**Input**:
- Query: `"Huawei"`
- Result: `"Hawaii Trading Company"`

**API Score**: 80 (token "Huawei" matches "Hawaii" with edits)

**Local Scores**:
- Token Set Ratio: 35 (completely different token sets: {"huawei"} vs {"hawaii", "trading", "company"})
- Jaro-Winkler: 62 (some character similarity between "Huawei" and "Hawaii")
- Levenshtein: 50 (moderate edit distance due to length difference)
- Token Sort: 38 (sorting doesn't help, different tokens)
- Phonetic: 70 (different pronunciation but some similarity)

**Local Score Calculation**:
```
local_score = (35×0.30) + (62×0.25) + (50×0.20) + (38×0.15) + (70×0.10)
            = 10.5 + 15.5 + 10.0 + 5.7 + 7.0
            = 48.7
```

**Combined Score**:
```
combined_score = (80 × 0.60) + (48.7 × 0.40)
               = 48 + 19.48
               = 67.48
```

**Match Quality**: **MEDIUM** ⚠️
(Local algorithms correctly downgrade false positive from HIGH to MEDIUM)

---

### Example 7: Strong False Positive Downgrade

**Input**:
- Query: `"Apple"`
- Result: `"Appleton Industries"`

**API Score**: 80 (token "Apple" partially matches "Appleton")

**Local Scores**:
- Token Set Ratio: 25 (very different token sets: {"apple"} vs {"appleton", "industries"})
- Jaro-Winkler: 58 (some prefix match but different overall)
- Levenshtein: 42 (significant difference)
- Token Sort: 28 (different even when sorted)
- Phonetic: 60 (different pronunciation)

**Local Score Calculation**:
```
local_score = (25×0.30) + (58×0.25) + (42×0.20) + (28×0.15) + (60×0.10)
            = 7.5 + 14.5 + 8.4 + 4.2 + 6.0
            = 40.6
```

**Combined Score**:
```
combined_score = (80 × 0.60) + (40.6 × 0.40)
               = 48 + 16.24
               = 64.24
```

**Match Quality**: **LOW** ❌
(Strong local penalty identifies poor match, downgrades to LOW)

---

### Example 8: Chinese Name Transliteration

**Input**:
- Query: `"Wang Wei"`
- Result: `"Wang Wey"` (different transliteration)

**API Score**: 90 (close match with minor edit)

**Local Scores**:
- Token Set Ratio: 92 (first token exact, second similar)
- Jaro-Winkler: 94 (very close strings)
- Levenshtein: 88 (1-2 character difference)
- Token Sort: 91 (similar after sorting)
- Phonetic: 100 (same pronunciation - this is where phonetic shines!)

**Local Score Calculation**:
```
local_score = (92×0.30) + (94×0.25) + (88×0.20) + (91×0.15) + (100×0.10)
            = 27.6 + 23.5 + 17.6 + 13.65 + 10.0
            = 92.35
```

**Combined Score**:
```
combined_score = (90 × 0.60) + (92.35 × 0.40)
               = 54 + 36.94
               = 90.94
```

**Match Quality**: **HIGH** ✅
(Phonetic matching helps identify transliteration variant)

---

## Scoring Pipeline Flowchart

```
┌─────────────────────┐
│  User Query Name    │
│  "Huawei Tech"      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  USA Trade API Query                │
│  (fuzzy_name=true)                  │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  API Returns Results with Score     │
│  [80, 90, or 100]                   │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  For Each Result:                   │
│  Calculate Local Similarity         │
│                                     │
│  1. Token Set Ratio (30%)          │
│  2. Jaro-Winkler (25%)             │
│  3. Levenshtein (20%)              │
│  4. Token Sort (15%)               │
│  5. Phonetic Match (10%)           │
│                                     │
│  local_score = weighted average     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Combine Scores                     │
│                                     │
│  combined = (api × 0.6) +           │
│             (local × 0.4)           │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Classify Match Quality             │
│                                     │
│  ≥ 92  → EXACT                      │
│  80-91 → HIGH                       │
│  65-79 → MEDIUM                     │
│  < 65  → LOW                        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Display to User                    │
│  - Combined Score                   │
│  - Match Quality Badge              │
│  - Similarity Breakdown (expandable)│
└─────────────────────────────────────┘
```

---

## Configuration

All scoring parameters are defined in `config.py`:

```python
FUZZY_MATCHING_CONFIG = {
    # Algorithm weights (sum to 1.0)
    "weights": {
        "token_set": 0.30,      # Company name variations
        "jaro_winkler": 0.25,   # Name matching with prefix bonus
        "levenshtein": 0.20,    # Edit distance baseline
        "token_sort": 0.15,     # Word order variations
        "phonetic": 0.10        # Pronunciation similarity
    },

    # Match quality thresholds
    "thresholds": {
        "exact": 92,      # High confidence exact match
        "high": 80,       # Strong fuzzy match
        "medium": 65,     # Moderate fuzzy match
        "low": 0          # Weak match / false positive
    },

    # Score combination weights (sum to 1.0)
    "api_weight": 0.60,     # API score weight (authoritative)
    "local_weight": 0.40    # Local score weight (refinement)
}
```

### Tuning Guidelines

**To reduce false positives** (more conservative):
- Increase `exact` threshold to 95
- Increase `high` threshold to 85
- Increase `token_set` weight to 0.35 (penalizes different token sets more)

**To catch more true positives** (more lenient):
- Decrease `exact` threshold to 90
- Decrease `high` threshold to 75
- Increase `jaro_winkler` weight to 0.30 (more forgiving of minor differences)

**To trust API more**:
- Increase `api_weight` to 0.70
- Decrease `local_weight` to 0.30

**To trust local algorithms more**:
- Decrease `api_weight` to 0.50
- Increase `local_weight` to 0.50

---

## Benefits of Hybrid System

1. **Granularity**: Continuous 0-100 scale instead of 3 discrete levels
2. **False Positive Reduction**: Poor matches (e.g., "Huawei" vs "Hawaii") get lower scores
3. **Transparency**: Users see why a match scored a certain way
4. **Tunability**: Weights and thresholds adjustable based on feedback
5. **Multi-dimensional**: Different algorithms catch different types of variations
6. **Respects API Authority**: 60% weight preserves API's judgment while adding refinement

---

## References

- **USA Trade API Documentation**: https://data.trade.gov/consolidated_screening_list
- **RapidFuzz Library**: https://github.com/maxbachmann/RapidFuzz
- **Jaro-Winkler Distance**: https://en.wikipedia.org/wiki/Jaro–Winkler_distance
- **Levenshtein Distance**: https://en.wikipedia.org/wiki/Levenshtein_distance
- **Double Metaphone**: https://en.wikipedia.org/wiki/Metaphone

---

**Last Updated**: 2026-02-24
**Version**: 1.0
