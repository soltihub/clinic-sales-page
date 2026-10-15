# Clinic ad-copy sales page

Five-block sales page for UAE clinics, with a validated free-sample form and a password-protected admin view at `/admin`.

## Run locally
`ADMIN_PASSWORD='your-password' python3 app.py`, then open http://localhost:8080

## Deploy on Railway
1. New project, then deploy from this GitHub repo.
2. Variables: `ADMIN_PASSWORD` (strong password) and `DB_PATH=/data/submissions.db`.
3. Add a Volume mounted at `/data` so submissions survive restarts.
4. Settings, Networking, Generate Domain.

Videos: add `videos/ad1.mp4` to `videos/ad5.mp4`.
