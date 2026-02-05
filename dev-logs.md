reference docs for usa api: https://developer.trade.gov/api-details#api=consolidated-screening-list&operation=search
reference for consolidated screenling list: https://www.trade.gov/consolidated-screening-list

jan 8 4:05pm
1. usa works, looped through pagination to get the full results.
2. getting started on china's agent using gemini CUA

notes:
1. check the govtech suite of products to see if i can use any of their api
2. to present to diana and show our interim progress
3. pause the china sanctions database work for now

features:
1. They want to be able to search for chinese names, have it automatically convert to english to be used to query the usa database
2. if the entity is not on the sanctions list, are they currently being investigated? are there any recent lobbying from law makers against this entity?
3. Besides a link to the sanctions list, they want a media press release article as well. 
4. if the entity is not on the sanctions list, are we able to research on the entity's collaborations and find out if any one they work with are on the sanctions list.
--
3 feb
1. added chinese to english name translation
2. reached the free limits of my own gemini api key, seeking alternatives now.
3. downloaded ollama to run models on my own machine and duckduckgo (free web search)
4. risk level low, sensititvity?

## THREAT LEVEL & CONFIDENCE CALCULATION

### Threat Level (Risk Classification)
Based on database match count, score, and media hits:

- **SAFE**: 0 database matches found (removed)
- **LOW**: Matches exist, but Max Score < 100 (fuzzy match, not exact) no sanctions, no media coverage
- **MID**: Exact Match (Score ≥ 100) + 0 or 1 Media Source (him here) no sanctions, some sentitive links, fuzzy matches not exact match require further investigation. Deepsekk is here.
- **HIGH**: Exact Match (Score ≥ 100) + 2 or more Media Sources (on sanctions)
- **VERY HIGH**: Huawei is here, alot of media coverage. more than 3 official news.

Logic flow: score refers to number of matches on database
1. If no matches → SAFE
2. Else if highest score < 100 → LOW
3. Else if score ≥ 100 AND media_count < 2 → MID
4. Else (score ≥ 100 AND media_count ≥ 2) → HIGH

### Confidence Score
Binary classification on presence of database matches:
- **HIGH**: Entity found in federal sanctions databases (1+ matches)
- **STANDARD**: No database matches (relies on general cross-reference/OSINT only)

5 feb
1. main company (conglomerates) not sanctioned but their subsidaries are, search the web, then search each entity on the database. find a way to list the results in a good manner. currently only optimised for one entity results not multiple. 
2. each subsidary, top ceo, diagram, an option to search each one. in tactical summary.
3. analysis reports from law firms, consultancies
4. be descriptive regarding the threat level
5. add disclaimer
6. Vadim Makarov-> is threat level safe, not on database but is involved, should reclassify. signals intel should include non-govt sources. maybe two tabs. 
7. [database update] tencent should be on the list, US department of war: DOD release list of chinese military companies in accordance wuth section 1260H (button to update) 
8. copy text button, email button, word, drop the pdf button -> just tactical summary _ fed reg info
9. rename signals intel to "news report"
10. rename tactical summary to "info summary"
rename federal reg to "entity list"
rename sentinels to "Entity Background Check Bot"
rename subject identifier to "entity name"
rename target params to "search params"
rename jursidictions to "country of origin"
rename operations archive to "search history"
rename process logs to "thinking process logs"
rename intel doss to "search results"
11. [database update] list of equipment and services covered by section 2 of the secure network act (federal communicatoons commission).
12. postpone china's database. 
13. report should be a longer (my own opinion)
14. status should say explicitly sanctioned or not sanctioned, only for exact matches. 



3 weeks time- last week of feb (MDDI-Diana)
2.5 weeks time- just KL and Q