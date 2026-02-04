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

SAFE: 0 Matches.

LOW: Matches exist, but Max Score < 100 (Not Exact).

MID: Exact Match (100) + 0 or 1 Media Source.

HIGH: Exact Match (100) + 2 or more Media Sources.