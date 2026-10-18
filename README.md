# Django with Docker and MySQL

## Start the development environment

Optionally copy `.env.example` to `.env` and replace the example passwords. The
Compose file also contains development defaults, so this step is not required
for a first local run.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open <http://localhost:8000/>. The MySQL data is stored in the named
`mysql_data` volume and survives container restarts. Database migrations run
automatically whenever the web container starts.

To create an administrator account:

```powershell
docker compose exec web python manage.py createsuperuser
```

To add the fictional local-news dataset used by the demo homepage:

```powershell
docker compose exec web python manage.py seed_demo_news
```

The command can be run repeatedly; it does not duplicate existing demo news.
Site identity, colors, and base font size can be changed in Django Admin under
**Website settings**.

To stop the containers:

```powershell
docker compose down
```

Use `docker compose down --volumes` only when you intentionally want to delete
the local MySQL data as well.

Outside Docker, the project continues to use SQLite unless `DB_ENGINE=mysql`
and the MySQL environment variables are set.
