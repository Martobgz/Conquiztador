# Conquiztador

A quiz-and-conquest game. Django REST Framework backend, React + Vite frontend.

## Requirements

- Python 3.13
- Node.js 24 (LTS)

## Project layout

```
Conquiztador/
├── backend/
│   ├── accounts/        # custom user, profile, auth API, tests
│   ├── config/          # settings, root urls, error envelope
│   ├── manage.py
│   └── requirements.txt
└── frontend/
    └── src/             # React screens and the API client
```

## Running the backend

```powershell
cd backend
py -3.13 -m venv .venv          # first time only
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/`.

## Running the frontend

In a second terminal:

```powershell
cd frontend
npm install                     # first time only
npm run dev
```

Open `http://localhost:5173/`. The Vite dev server proxies `/api` to Django, so
the browser sees one origin and the session and CSRF cookies work without CORS.

## Running the backend tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py test accounts
```

## Django admin

`User` and `Profile` are registered in the admin at `/admin/`. Create an
account to log in with:

```powershell
python manage.py createsuperuser
```

## Authentication API

Session authentication. Every unsafe method needs an `X-CSRFToken` header;
`GET /api/auth/csrf/` sets the `csrftoken` cookie.

| Method | Endpoint             | Access        | Success          |
| ------ | -------------------- | ------------- | ---------------- |
| GET    | `/api/auth/csrf/`    | Public        | `204 No Content` |
| POST   | `/api/auth/register/`| Public        | `201 Created`    |
| POST   | `/api/auth/login/`   | Public        | `200 OK`         |
| POST   | `/api/auth/logout/`  | Authenticated | `204 No Content` |
| GET    | `/api/auth/me/`      | Authenticated | `200 OK`         |
| PATCH  | `/api/auth/me/`      | Authenticated | `200 OK`         |

`PATCH /api/auth/me/` accepts `nickname` and `avatar_key` only. The current
user always comes from the session, never from the URL or the request body.

Errors use one shape everywhere:

```json
{
  "errors": {
    "email": ["User with this email already exists."],
    "password_confirm": ["Passwords do not match."]
  }
}
```

## Milestones

| Tag        | Milestone                   |
| ---------- | --------------------------- |
| `m0-setup` | Initial project setup       |
| `m1-auth`  | Authentication and users    |
