# Clinic ad-copy sales page

Five-block sales page for UAE clinics, with a validated free-sample form and a password-protected admin view for reviewing every request by hand.

## Live site
- Site: https://clinicadsuae.pythonanywhere.com
- Admin: https://clinicadsuae.pythonanywhere.com/admin (username: `admin`)
- Hosting: PythonAnywhere free account `clinicadsuae`

## Files
- `app.py`: the sales page, form validation and admin view
- `wsgi_app.py`: connects the app to PythonAnywhere
- `Procfile`, `requirements.txt`: only used for other hosts like Railway

## Keep the site online
Free sites switch off after one month. Log in to PythonAnywhere, open the **Web** tab and click **Run until 1 month from today**. PythonAnywhere emails a reminder a week before.

## Update the site
1. Edit `app.py` on your PC and upload it here.
2. Upload the same file in PythonAnywhere under **Files**, `/home/clinicadsuae/clinic`.
3. On the **Web** tab, click **Reload**.

## Run locally (Windows PowerShell)
`$env:ADMIN_PASSWORD="your-password"; py app.py`, then open http://localhost:8080

## Security
Never put the admin password in this repo. It lives only in the PythonAnywhere WSGI file.
