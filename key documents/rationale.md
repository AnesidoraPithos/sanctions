this project creates a web application that allows staff working in international relations run background check research on certain entities. 

presently, a stakeholder will provide staff names of entities that they want to know: 'is there any risk working, collaborating or being associated to that entity?', and 'what is the extent of the risks involved? first-order, second-order?'. they are particularly concerned about how USA views the entity.

the web application houses a research agent that runs all the work on the backend, checking sanctions databases and a local database that is automatically updated (any remaining sanction lists not included in the main consolidated screening api provided by the USA.). it also does a duckduckgo search on the entity for any publically available internet information.

if the entity is a conglomerate/parent company, it searches through SEC EDGAR files for its subsidaries. it supplements the reserach with duckduckgo.

if the entity is a child of a conglomerate, it then searches for its sister companies. it supplements the reserach with duckduckgo.

it also maps the financial flow based on SEC EDGAR files on loan arrangements, what stakeholder % is owned by who, etc. it supplements the reserach with duckduckgo.

then creates a map to visualise this hierarchy structure.

you are able to select parents/sisters/subsidaries and add them to the search.

it creates a research report on the entitiy (and any selected ones) and searches for media sources on it (both government and general) and assigns a risk level for the entity.

it allows you to save the search findings to be retrieved in the future. 

