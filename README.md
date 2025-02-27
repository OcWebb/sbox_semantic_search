# S&Box Semantic Search backend API
This is the backend API powering [frontend](https://sbox.semanticsearches.net/) ([Code](https://github.com/OcWebb/sbox-semantic-search-web-frontend)) and the in editor [widget](https://github.com/OcWebb/sbox-semantic-search-browser-widget).

Technology used:
- OpenAI's text-embedding-3-small embedding model.
- PineconeDB
- FastAPI
- Dockerfile

## Features
- Update endpoint scans facepunches API for all packages updated or created since last run. This can be called on a cronjob.
- Search endpoint takes a query, take, skip and returns an array of packages in order of their semantic relevance.
