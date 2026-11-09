# Deploying Thriver

Three ways to run the backend, easiest first. The Flutter app is built
separately and pointed at whichever API URL you end up with.

## 1. Everything in Docker (local)

```
docker compose up --build
```

API at http://localhost:8000, docs at `/docs`, admin dashboard at
`/admin-dashboard/`. The first start creates the tables and seeds three demo
malls; restarts keep your data (volume `pgdata`). `docker compose down -v`
wipes it.

## 2. Free cloud deploy (Render API + database, Netlify web app)

### API and database
1. Push this repo to GitHub.
2. Render dashboard > **New > Blueprint** > pick the repo. It reads
   `render.yaml` and creates the database and the API.
3. When asked for `ALLOWED_ORIGINS`, enter your web app URL with no trailing
   slash (you will know it after step "Web app"; you can also set it later in
   the service's Environment tab and redeploy).
4. Wait for the deploy, then open `https://<your-service>.onrender.com/health`.
   You should see `{"status":"ok"}`.

`SECRET_KEY` and `ADMIN_SIGNUP_SECRET` are generated for you; read the admin
secret from the service's Environment tab when you want to create an admin.

The backend refuses to start with `ENV=production` if the secret is a default
or `ALLOWED_ORIGINS` is `*`. That is deliberate.

Free-tier caveat: the API sleeps after ~15 minutes idle and the first request
afterwards can take 30-60 seconds. Say so in your README so a reviewer doesn't
think it is broken. The free Render database is also time-limited, so check
Render's current terms before relying on it long term.

### Web app
```
cd mobile/thriver_app
flutter build web --release --dart-define=API_BASE_URL=https://<your-service>.onrender.com
```
Upload `build/web` to Netlify (drag and drop in the dashboard) or Vercel. Then
put that site's URL into `ALLOWED_ORIGINS` on Render and redeploy. Without
this the browser blocks every API call (CORS), and the app looks empty.

### Android APK
```
flutter build apk --release --dart-define=API_BASE_URL=https://<your-service>.onrender.com
```
Output: `build/app/outputs/flutter-apk/app-release.apk`. Sideload it; it is not a
Play Store build.

## 3. Live demo data

A deployed database has no recent activity, so forecasts say "unknown". Run
the simulator against it from your laptop:

```
export DATABASE_URL="<Render external database URL>"
python simulator/parking_sensor.py --fill-bias 0.8 --interval 5
```
or call `python -m scripts.backfill_activity` with the same `DATABASE_URL`
set (from `backend/`) for synthetic, labelled history.

## Environment variables

| Name | Purpose |
|---|---|
| `DATABASE_URL` | Postgres URL (`postgres://` is accepted and rewritten) |
| `ENV` | `production` turns on the safety checks below |
| `SECRET_KEY` | JWT signing key, 32+ random characters in production |
| `ADMIN_SIGNUP_SECRET` | Value a user must send to register as admin |
| `ALLOWED_ORIGINS` | Comma-separated front-end origins, no trailing slash |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default 60 |
| `PORT` | Set by the host; the container honours it |
