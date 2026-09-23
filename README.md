# resume-bot

Querying the web:
searxng
Camoufox - anti bot blocking

searxng seems to have a lag behind google

## todo

- store results in postgres db
- fetch all queries without getting ip blocked

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
