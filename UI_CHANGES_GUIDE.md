# UI Changes Guide - Configurable Search Limits

## Overview
This guide shows the before/after UI changes for the configurable search limits feature.

---

## 1. SEARCH FORM - Network Tier Configuration

### BEFORE (Hidden Limits)
```
┌─────────────────────────────────────────────────┐
│ Network Tier Configuration                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ Search Depth: 2 levels                         │
│ [────●──────────] (1-3)                        │
│                                                 │
│ Ownership Threshold: 50%                       │
│ [─────────●─────] (0-100%)                     │
│                                                 │
│ ☑ Include sister companies                     │
│                                                 │
│ ❌ NO VISIBILITY OF SEARCH LIMITS              │
│ ❌ NO CONTROL OVER LIMITS                      │
└─────────────────────────────────────────────────┘
```

### AFTER (Configurable Limits) ✅
```
┌─────────────────────────────────────────────────┐
│ Network Tier Configuration                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ Search Depth: 2 levels                         │
│ [────●──────────] (1-3)                        │
│                                                 │
│ Ownership Threshold: 50%                       │
│ [─────────●─────] (0-100%)                     │
│                                                 │
│ ☑ Include sister companies                     │
│                                                 │
│ ✅ Max Level 2 Searches: 20                    │
│ [────────●──────────────] (5-50)               │
│ 5 (fastest)  25 (balanced)  50 (comprehensive) │
│ ℹ️  Only top 20 subsidiaries by ownership %    │
│    will be searched. Higher values may timeout. │
│                                                 │
│ [Appears when depth = 3:]                      │
│ ✅ Max Level 3 Searches: 10                    │
│ [────●──────────] (5-30)                       │
│ 5 (fastest)  15 (balanced)  30 (comprehensive) │
│ ⚠️  Higher values significantly increase time.  │
└─────────────────────────────────────────────────┘
```

**Key Changes**:
- ✅ New "Max Level 2 Searches" slider (5-50, default: 20)
- ✅ New "Max Level 3 Searches" slider (5-30, default: 10)
- ✅ Conditional rendering (only show when relevant depth selected)
- ✅ Clear help text and warnings
- ✅ Visual feedback on speed vs coverage trade-offs

---

## 2. RESULTS PAGE - Search Information Banner

### BEFORE (No Limit Visibility)
```
┌─────────────────────────────────────────────────┐
│ ℹ️ Network Tier Research Completed              │
├─────────────────────────────────────────────────┤
│ Multi-level corporate structure analysis        │
│ performed (2 levels deep).                      │
│                                                 │
│ Discovered 35 entities (30 level 1, 5 level 2).│
│                                                 │
│ Data sources checked:                          │
│ SEC EDGAR, Wikipedia, DuckDuckGo               │
│                                                 │
│ ❌ NO INDICATION OF WHAT LIMITS WERE USED      │
└─────────────────────────────────────────────────┘
```

### AFTER (Limits Displayed) ✅
```
┌─────────────────────────────────────────────────┐
│ ℹ️ Network Tier Research Completed              │
├─────────────────────────────────────────────────┤
│ Multi-level corporate structure analysis        │
│ performed (2 levels deep).                      │
│                                                 │
│ Discovered 35 entities (30 level 1, 5 level 2).│
│                                                 │
│ Data sources checked:                          │
│ SEC EDGAR, Wikipedia, DuckDuckGo               │
│                                                 │
│ ✅ Search limits:                               │
│    Top 20 subsidiaries searched for level 2    │
│                                                 │
└─────────────────────────────────────────────────┘
```

**For Depth 3**:
```
│ ✅ Search limits:                               │
│    Top 20 subsidiaries searched for level 2,   │
│    top 10 for level 3                          │
```

**Key Changes**:
- ✅ New line showing active limits used in search
- ✅ Shows actual configured values (not just defaults)
- ✅ Backwards compatible (shows defaults for old searches)

---

## 3. WARNINGS SECTION

### BEFORE (Generic Message)
```
┌─────────────────────────────────────────────────┐
│ ⚠️ Data Source Limitations                      │
├─────────────────────────────────────────────────┤
│ • Limited level 2 search to top 20 subsidiaries│
│   by ownership (out of 111 total) to prevent   │
│   timeout                                       │
│                                                 │
│ ❌ ALWAYS SHOWS "20" (HARDCODED)                │
└─────────────────────────────────────────────────┘
```

### AFTER (Dynamic Values) ✅
```
┌─────────────────────────────────────────────────┐
│ ⚠️ Data Source Limitations                      │
├─────────────────────────────────────────────────┤
│ • Limited level 2 search to top 15 subsidiaries│
│   by ownership (out of 111 total) to prevent   │
│   timeout                                       │
│                                                 │
│ ✅ SHOWS ACTUAL USER-CONFIGURED VALUE (15)      │
└─────────────────────────────────────────────────┘
```

**Key Changes**:
- ✅ Warning messages now use actual configured limits
- ✅ Accurate reflection of what was searched

---

## 4. USER WORKFLOW COMPARISON

### BEFORE (No Control)
```
1. User selects "Network Tier"
2. User sets depth to 2
3. ❌ No visibility of limits
4. User clicks "Search"
5. [Search runs with hardcoded limit of 20]
6. ⚠️ User sees warning AFTER: "Limited to 20"
7. 😞 User surprised by limitation
```

### AFTER (Full Control) ✅
```
1. User selects "Network Tier"
2. User sets depth to 2
3. ✅ "Max Level 2 Searches" slider appears
4. ✅ User sees default (20) and help text
5. ✅ User can adjust based on needs:
   - Speed priority → reduce to 5-10
   - Coverage priority → increase to 40-50
6. ✅ Help text warns about timeouts
7. User clicks "Search"
8. [Search runs with user's chosen limit]
9. ✅ Results show: "Search limits: Top [N]..."
10. ✅ Warnings use actual value: "Limited to [N]"
11. 😊 User has full understanding and control
```

---

## 5. SLIDER EXAMPLES

### Level 2 Slider Configuration
```
Max Level 2 Searches: 20
[5]─────[10]─────[15]─────[20]─────[25]─────[30]─────[35]─────[40]─────[45]─────[50]
 │       │        │        │        │        │        │        │        │        │
Fast    Quick   Medium  Balanced  Good    Thorough  Detailed  Deep  Extensive  Max
~30s    ~1min   ~1.5min  ~2min   ~2.5min   ~3min    ~3.5min  ~4min  ~4.5min   ~5min

└── Speed ──────────────────────────────────────────────── Coverage ──┘
```

### Level 3 Slider Configuration
```
Max Level 3 Searches: 10
[5]─────[10]─────[15]─────[20]─────[25]─────[30]
 │       │        │        │        │        │
Fast  Balanced  Good   Thorough  Detailed  Max
Sample Default  Coverage  Deep    Extensive Very Deep

⚠️ WARNING: Level 3 is exponential - higher values compound significantly!
```

---

## 6. RESPONSIVE BEHAVIOR

### When Depth = 1 (Level 1 only)
```
No limit sliders shown
(Limits only apply to level 2+ searches)
```

### When Depth = 2 (Level 1 + Level 2)
```
✅ "Max Level 2 Searches" slider appears
❌ "Max Level 3 Searches" slider hidden
```

### When Depth = 3 (All levels)
```
✅ "Max Level 2 Searches" slider appears
✅ "Max Level 3 Searches" slider appears
```

---

## 7. HELP TEXT EXAMPLES

### Level 2 Help Text
```
ℹ️  To prevent timeouts, only the top N subsidiaries by ownership %
   will be searched for level 2.
⚠️  Higher values may timeout for large companies.
```

### Level 3 Help Text
```
ℹ️  To prevent timeouts, only the top N level 2 subsidiaries will be
   searched for level 3.
⚠️  Higher values significantly increase search time.
```

---

## 8. EXAMPLE: Searching Alibaba

### Scenario A: Default Limits (Balanced)
```
Configuration:
• Depth: 2 levels
• Max Level 2: 20 (default)

Results:
• 111 level 1 subsidiaries found
• ✅ Top 20 searched for level 2 (sorted by ownership %)
• 5 level 2 subsidiaries found
• ⚠️ Warning: "Limited to top 20 by ownership (out of 111 total)"
• ⏱️  Search time: ~2 minutes
```

### Scenario B: Increased Limit (More Coverage)
```
Configuration:
• Depth: 2 levels
• Max Level 2: 50 (user increased)

Results:
• 111 level 1 subsidiaries found
• ✅ Top 50 searched for level 2
• 15 level 2 subsidiaries found (3× more!)
• ⚠️ Warning: "Limited to top 50 by ownership (out of 111 total)"
• ⏱️  Search time: ~5 minutes (2.5× longer)
```

### Scenario C: Reduced Limit (Faster)
```
Configuration:
• Depth: 2 levels
• Max Level 2: 5 (user reduced)

Results:
• 111 level 1 subsidiaries found
• ✅ Top 5 searched for level 2
• 2 level 2 subsidiaries found
• ⚠️ Warning: "Limited to top 5 by ownership (out of 111 total)"
• ⏱️  Search time: ~30 seconds (4× faster!)
```

---

## 9. COLOR CODING

### Slider Labels
- **Blue**: Current value (e.g., "20" in "Max Level 2 Searches: 20")
- **Gray**: Label text and help text
- **Yellow**: Warning text (e.g., "may timeout")

### Results Banner
- **Blue background**: Information banner
- **Blue text**: Main message
- **Light blue**: Secondary info (data sources, limits)

### Warnings Banner
- **Yellow background**: Warning banner
- **Yellow icon**: ⚠️
- **Yellow text**: Warning messages

---

## 10. ACCESSIBILITY

✅ **Keyboard Navigation**:
- Sliders fully keyboard-accessible (arrow keys to adjust)
- Tab navigation through all controls

✅ **Screen Readers**:
- Labels properly associated with inputs
- Help text read after label
- ARIA labels on sliders

✅ **Visual Feedback**:
- Clear visual distinction between active/inactive
- High contrast colors
- Current value prominently displayed

---

## Summary

### What Changed
1. ✅ **Two new sliders** in Network Tier Configuration
2. ✅ **Search limits display** in results banner
3. ✅ **Dynamic warning values** reflecting actual limits
4. ✅ **Conditional rendering** (only show when relevant)
5. ✅ **Help text and warnings** for user guidance

### User Benefits
- 🎯 **Transparency**: See limits BEFORE searching
- 🎛️ **Control**: Adjust based on needs (speed vs coverage)
- 📊 **Understanding**: Clear trade-offs explained
- ⏱️ **Time management**: Choose appropriate limits for use case
- 🔄 **Flexibility**: Different limits for different searches

### Technical Benefits
- 🔧 **Backwards compatible**: Defaults match previous behavior
- ✅ **Type-safe**: Full TypeScript validation
- 🛡️ **Server-side validation**: Pydantic models enforce ranges
- 📦 **Clean architecture**: Changes flow through entire stack
- 🧪 **Testable**: Clear test cases for verification
