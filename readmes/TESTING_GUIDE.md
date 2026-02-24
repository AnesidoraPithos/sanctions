# Testing Guide - Fuzzy Matching Score System

## Quick Start

Run the application and test the new fuzzy matching system:

```bash
cd "/Users/faith/Desktop/IMDA/International/sanctions free"
streamlit run app.py
```

---

## Test Scenarios

### Test 1: Perfect Exact Match ✅

**Input**: `Huawei`

**Expected Results**:
- Multiple results with **EXACT** (green) or **HIGH** (blue) badges
- Combined scores near **92+** for exact matches
- API score **100** for perfect matches
- Token Set Ratio should be **95-100** for true matches

**What to Look For**:
- ✓ Green EXACT badges on true "Huawei" entities
- ✓ Combined score aligns with visual badge
- ✓ Expandable breakdown shows high scores across all algorithms

**Success Criteria**: True Huawei entities show EXACT/HIGH classification

---

### Test 2: False Positive Detection ⚠️

**Input**: `Huawei`

**Expected Results**:
- If "Hawaii" or similar sounding names appear, they should have **LOW** (gray) or **MEDIUM** (yellow) badges
- Combined score **< 70** for false positives
- Token Set Ratio should be **very low (< 40)** for false positives

**What to Look For**:
- ✓ "Hawaii Trading Company" (if exists) gets LOW badge
- ✓ Combined score significantly lower than API score
- ✓ Expandable breakdown shows:
  - Token Set: Low (different token sets)
  - Jaro-Winkler: Moderate (character similarity)
  - Levenshtein: Low (many edits needed)

**Success Criteria**: False positives correctly identified with LOW/MEDIUM classification

---

### Test 3: Legal Suffix Variations ✅

**Input**: `Apple`

**Expected Results**:
- "Apple Inc", "Apple Incorporated", "Apple Computer Inc" should all get **EXACT** or **HIGH** badges
- Token Set Ratio should be **high (90+)** despite different suffixes
- Combined scores should be **85+**

**What to Look For**:
- ✓ Legal suffixes (Inc, Ltd, Corp, LLC) don't significantly lower scores
- ✓ Token Set algorithm handles extra words well
- ✓ All variations of same company cluster around similar scores

**Success Criteria**: Legal variations recognized as same entity

---

### Test 4: Typo Handling 🔧

**Input**: Search for any entity with common typos

**Expected Results**:
- Minor typos (1-2 character difference) should get **HIGH** badge
- Jaro-Winkler score should be **high (85+)**
- Combined score should be **80-92**

**What to Look For**:
- ✓ Typos don't get marked as LOW
- ✓ Jaro-Winkler and Levenshtein scores are high
- ✓ System correctly identifies as close match, not false positive

**Success Criteria**: Legitimate typos classified as HIGH, not LOW

---

### Test 5: Partial Name Matches 🔍

**Input**: `Huawei Tech` (shortened query)

**Expected Results**:
- "Huawei Technologies Ltd" should get **HIGH** or **MEDIUM** badge
- Token Set should recognize partial token match
- Combined score should be **70-85**

**What to Look For**:
- ✓ Partial matches don't get EXACT classification
- ✓ System recognizes similarity but shows it's not perfect
- ✓ Token Set Ratio is moderate (60-80)

**Success Criteria**: Partial matches correctly identified as HIGH/MEDIUM

---

### Test 6: Completely Different Entities ❌

**Input**: `Apple`

**Check if results include**: "Appleton Industries" or similar

**Expected Results**:
- Unrelated entities should get **LOW** or **MEDIUM** badge
- Combined score should be **< 70**
- Token Set Ratio should be **very low (< 50)**

**What to Look For**:
- ✓ "Appleton" vs "Apple" gets downgraded from API score 80
- ✓ Local algorithms catch the difference
- ✓ Visual badge warns user this is weak match

**Success Criteria**: Unrelated entities correctly downgraded to LOW/MEDIUM

---

### Test 7: Chinese Name Transliteration 🌏

**Input**: Chinese name (if available in your database)

**Expected Results**:
- Different transliterations of same name should get **HIGH** badge
- Phonetic Match algorithm should help
- Combined score should be **80+** for valid transliterations

**What to Look For**:
- ✓ Phonetic Match score is 100 for same pronunciation
- ✓ Other algorithms may show moderate scores
- ✓ System recognizes transliteration variants

**Success Criteria**: Transliteration variants properly matched

---

## Visual Inspection Checklist

### ✅ Match Quality Badges
- [ ] EXACT badge is **green** with ✓ icon
- [ ] HIGH badge is **blue** with ⚡ icon
- [ ] MEDIUM badge is **yellow** with ⚠ icon
- [ ] LOW badge is **gray** with ? icon

### ✅ Score Display
- [ ] Combined Score is prominently displayed
- [ ] API Score is shown
- [ ] Local Score is shown
- [ ] Format: "COMBINED SCORE: XX | API: XX | Local: XX"

### ✅ Expandable Breakdown
- [ ] "📊 View Detailed Similarity Breakdown" expander exists
- [ ] Clicking expands to show all 5 algorithm scores
- [ ] Formula is displayed with actual values
- [ ] Threshold explanations are shown

### ✅ Alignment
- [ ] Badge color matches score range
- [ ] EXACT (≥92) → Green
- [ ] HIGH (80-91) → Blue
- [ ] MEDIUM (65-79) → Yellow
- [ ] LOW (<65) → Gray

---

## Functional Testing

### Test A: Query Without Fuzzy Matching

**Steps**:
1. Enter entity name
2. **Uncheck** "Enable Fuzzy Matching"
3. Run search

**Expected**:
- Results should still show match quality badges
- Combined scores should be calculated
- Only exact/near-exact matches returned

**Success**: Fuzzy matching toggle works correctly

---

### Test B: Query With Fuzzy Matching

**Steps**:
1. Enter entity name
2. **Check** "Enable Fuzzy Matching"
3. Run search

**Expected**:
- More results returned (including fuzzy matches)
- Mix of EXACT/HIGH/MEDIUM/LOW badges
- False positives clearly marked with LOW badges

**Success**: Fuzzy matching returns broader results with quality indicators

---

### Test C: Empty Query Handling

**Steps**:
1. Leave entity name blank
2. Run search

**Expected**:
- Appropriate error message or no results
- No crashes or exceptions

**Success**: Graceful handling of edge cases

---

### Test D: Special Characters

**Steps**:
1. Enter entity name with special characters: `"Tech Co., Ltd."`
2. Run search

**Expected**:
- System handles punctuation correctly
- Tokens are properly parsed
- Scores are calculated accurately

**Success**: Special characters don't break scoring

---

## Verification with Test Cases

Run the built-in test cases:

```bash
python3 matching_utils.py
```

**Expected Output**:
```
================================================================================
FUZZY MATCHING TEST CASES
================================================================================

Perfect exact match
Query: 'Huawei' → Result: 'Huawei'
API Score: 100
Local Score: 100.0
Combined Score: 100.0
Match Quality: EXACT
Breakdown: {'token_set': 100.0, 'jaro_winkler': 100.0, 'levenshtein': 100.0, 'token_sort': 100.0, 'phonetic': 100.0}
--------------------------------------------------------------------------------

... (more test cases) ...

False positive caught
Query: 'Huawei' → Result: 'Hawaii Trading Company'
API Score: 80
Local Score: 33.98
Combined Score: 61.59
Match Quality: LOW
Breakdown: {'token_set': 28.57, 'jaro_winkler': 61.62, 'levenshtein': 28.57, 'token_sort': 28.57, 'phonetic': 0.0}
--------------------------------------------------------------------------------
```

**Success Criteria**:
- ✓ All 6 test cases run without errors
- ✓ False positive (Hawaii) gets LOW classification
- ✓ Exact matches get EXACT classification
- ✓ Scores align with expected ranges

---

## Performance Testing

### Test P1: Response Time

**Steps**:
1. Search for common entity (e.g., "Huawei")
2. Note time to display results

**Expected**:
- Additional local scoring adds **< 2 seconds** to total time
- UI remains responsive
- No noticeable lag when expanding breakdowns

**Success**: Performance impact is minimal

---

### Test P2: Large Result Sets

**Steps**:
1. Search for broad term that returns 100+ results
2. Verify all results load

**Expected**:
- All results show match quality badges
- Combined scores calculated for all
- No timeouts or crashes

**Success**: System scales to large result sets

---

## Edge Case Testing

### Edge 1: Single Character Names

**Input**: Single character entity name (if exists)

**Expected**:
- Scores may be lower than usual
- System doesn't crash
- Match quality still classified correctly

---

### Edge 2: Very Long Names

**Input**: Entity with very long name (50+ characters)

**Expected**:
- All algorithms handle long strings
- Scores calculated accurately
- UI displays full name properly

---

### Edge 3: Numbers in Names

**Input**: Entity name with numbers (e.g., "Bank 123")

**Expected**:
- Numbers treated as tokens
- Scoring works correctly
- No parsing errors

---

## Regression Testing

### Verify Existing Functionality

- [ ] Basic search still works
- [ ] Country filter still works
- [ ] Media/OSINT tab still works
- [ ] Risk level calculation still works
- [ ] History tab still works
- [ ] PDF export still works

**Success**: New features don't break existing functionality

---

## Documentation Verification

### Check All Documentation Files

- [ ] `SCORING_SYSTEM.md` exists and is comprehensive
- [ ] `IMPLEMENTATION_SUMMARY.md` exists
- [ ] `UI_PREVIEW.md` exists
- [ ] `TESTING_GUIDE.md` exists (this file)
- [ ] `requirements.txt` includes rapidfuzz and metaphone

---

## Bug Reporting Template

If you find issues, document them with:

```markdown
**Test Case**: [Which test scenario]
**Input**: [What you searched for]
**Expected**: [What should happen]
**Actual**: [What actually happened]
**Screenshot**: [If applicable]
**Steps to Reproduce**:
1. Step 1
2. Step 2
3. ...

**Environment**:
- Python version:
- Streamlit version:
- rapidfuzz version:
```

---

## Final Acceptance Criteria

### ✅ Core Functionality
- [ ] All 6 test scenarios pass
- [ ] Match quality badges display correctly
- [ ] Combined scores calculated accurately
- [ ] Expandable breakdowns show detailed info

### ✅ False Positive Detection
- [ ] "Hawaii" vs "Huawei" correctly identified as LOW
- [ ] "Appleton" vs "Apple" correctly downgraded
- [ ] Token Set Ratio catches different token sets

### ✅ True Positive Recognition
- [ ] Exact matches get EXACT badge (green)
- [ ] Close typos get HIGH badge (blue)
- [ ] Legal suffix variations recognized as same entity

### ✅ User Experience
- [ ] Color coding is intuitive
- [ ] Expandable sections provide transparency
- [ ] Scores align with visual indicators
- [ ] Documentation is clear and helpful

### ✅ Performance
- [ ] Response time < 2 seconds added overhead
- [ ] No crashes with large result sets
- [ ] UI remains responsive

### ✅ Integration
- [ ] Risk level calculation uses combined scores
- [ ] Existing features still work
- [ ] Database operations unaffected

---

## Next Steps After Testing

1. **If all tests pass**: System is ready for production use ✅
2. **If minor issues**: Document and create fix plan 🔧
3. **If tuning needed**: Adjust config.py weights/thresholds ⚙️
4. **If major issues**: Review implementation and consult documentation 📚

---

**Testing Date**: _____________
**Tested By**: _____________
**Status**: ⬜ Pass  ⬜ Fail  ⬜ Needs Tuning
**Notes**:
