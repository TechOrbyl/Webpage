# ORBYL FastAPI backend

## Setup

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Put the Neon connection string in `.env`:

   ```env
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```

3. Start the server from the project root:

   ```powershell
   uvicorn backend.main:app --reload
   ```

The site is available at http://127.0.0.1:8000 and the admin dashboard at http://127.0.0.1:8000/admin.

The default demo credentials are:

- Username: `admin`
- Password: `orbyl2026`

Change these values in `.env` before deployment. The admin page is intended as a lightweight internal dashboard; add a production identity provider, HTTPS, rate limiting, and stronger secrets before exposing it publicly.
