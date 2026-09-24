# resume-bot

Querying the web:
searxng
Camoufox - anti bot blocking

## todo

- fetch all queries without getting ip blocked
- Separate search searxng logic and parsing logic into dif files so any query can be searched and the results returned. Logic can be changed without breaking anything. can use search for future agent search.

- Increase delays into the minutes.

- Auto detect rate limiting by checking the searxng logs.

- Rotate proxies if rate limited.

- Add camoufox for future agent use.

### Setup:

#### Start local searxng docker instance:

`docker compose up -d`

#### run python script:

python main.py

#### kill searxng docker instance

docker compose down

#### useful docs:

searxng search settings.yml https://docs.searxng.org/admin/settings/settings_search.html
searxng docker setup https://docs.searxng.org/admin/installation-docker.html
