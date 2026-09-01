# Mini CRM — Lead & Client Management System

A full-stack customer relationship management application for organizing companies, contacts, sales opportunities, tasks, meetings, and notes in one responsive workspace.

Mini CRM combines a FastAPI and PostgreSQL backend with a Next.js frontend, JWT authentication, role-based permissions, analytics, audit history, notifications, CSV data transfer, and advanced lead filtering.

## Features

### CRM workspace

* Manage companies and their associated contacts.
* Track leads through `New`, `Contacted`, `Qualified`, `Won`, and `Lost` stages.
* Record estimated deal values, lead sources, expected close dates, and descriptions.
* Create and manage tasks, meetings, and notes.
* Search CRM records from a centralized search interface.
* Use responsive desktop tables and mobile-friendly cards.

### Sales analytics

* Monitor company, contact, lead, task, and meeting totals.
* Review open and weighted pipeline values.
* Compare pipeline distribution and value by lead stage.
* Track won value, average open-deal value, and closed-lead win rate.
* Monitor task completion, overdue work, due dates, and upcoming meetings.

### Advanced lead filtering

* Search lead titles, sources, and descriptions.
* Filter by stage, company, and contact.
* Filter by minimum and maximum estimated value.
* Filter by expected-close date range.
* Sort by newest, oldest, deal value, or nearest expected close.
* Combine multiple filters in one request.

### Enterprise capabilities

* Secure registration and login using JWT access tokens.
* Argon2 password hashing.
* Role-based authorization for privileged actions.
* Administrative user management.
* In-app notifications with unread-count tracking.
* Activity and audit logs for important CRM changes.
* CSV preview, validation, import, and export for companies, contacts, and leads.
* Protected backend routes and configurable CORS origins.

## Technology Stack

| Layer          | Technologies                                     |
| -------------- | ------------------------------------------------ |
| Frontend       | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend        | FastAPI, Python, Pydantic Settings               |
| Database       | PostgreSQL, SQLAlchemy 2                         |
| Migrations     | Alembic                                          |
| Authentication | JWT and Argon2                                   |
| Testing        | Pytest and FastAPI TestClient                    |
| Code quality   | ESLint, TypeScript, Next.js production build     |

## Project Structure

```text
mini-crm/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route modules
│   │   ├── core/             # Authentication, activity, and CSV services
│   │   ├── crud/             # Database queries and mutations
│   │   ├── models/           # SQLAlchemy models
│   │   └── schemas/          # Pydantic schemas
│   ├── migrations/           # Alembic migrations
│   ├── tests/                # Backend test suite
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # Reusable interface components
│   ├── hooks/                # React hooks
│   ├── lib/                  # API clients and utilities
│   ├── types/                # TypeScript types
│   └── package.json
└── README.md
```

## Prerequisites

Install the following before running the project:

* Git
* Python 3.11 or newer
* Node.js 20.9 or newer
* PostgreSQL

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/areeba-munir/mini-crm.git
cd mini-crm
```

### 2. Create PostgreSQL databases

Create one database for development and another for automated tests:

```sql
CREATE DATABASE mini_crm;
CREATE DATABASE mini_crm_test;
```

Keep the development and test databases separate because the test suite modifies test data.

### 3. Configure the backend

Move into the backend directory:

```powershell
cd backend
```

Create and activate a virtual environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the backend dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `backend/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mini_crm
DB_TEST_NAME=mini_crm_test
DB_USER=postgres
DB_PASSWORD=your_postgresql_password

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Generate a secure JWT secret if needed:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Apply the database migrations:

```bash
alembic upgrade head
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

The API will normally run at:

```text
http://127.0.0.1:8000
```

### 4. Configure the frontend

Open another terminal from the repository root:

```powershell
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

Start the frontend:

```bash
npm run dev
```

Open the application at:

```text
http://localhost:3000
```

## API Documentation

With the backend running, interactive API documentation is available at:

* Swagger UI: http://127.0.0.1:8000/docs
* ReDoc: http://127.0.0.1:8000/redoc

Protected endpoints require a bearer access token obtained through authentication.

## Main Application Pages

| Page             | Purpose                                                                     |
| ---------------- | --------------------------------------------------------------------------- |
| `/dashboard`     | CRM totals, revenue analytics, pipeline distribution, and upcoming activity |
| `/companies`     | Company records and management actions                                      |
| `/contacts`      | Contact records and company relationships                                   |
| `/leads`         | Sales pipeline, advanced filters, sorting, and lead actions                 |
| `/tasks`         | Work tracking, deadlines, and completion status                             |
| `/meetings`      | Scheduled customer and sales meetings                                       |
| `/notes`         | CRM notes and related records                                               |
| `/notifications` | In-app notification center                                                  |
| `/activities`    | Activity and audit history                                                  |
| `/data-transfer` | CSV preview, import, and export workspace                                   |
| `/users`         | Authorized user administration                                              |
| `/search`        | Cross-CRM record search                                                     |
| `/profile`       | Current-user profile information                                            |

## Testing

### Backend

Activate the backend virtual environment and install the testing tools if needed:

```powershell
cd backend
python -m pip install pytest httpx
python -m pytest -q
git diff --check
```

The latest verified backend run contains **258 passing tests**.

### Frontend

```powershell
cd frontend
npm run lint
npm run build
git diff --check
```

Both ESLint and the optimized Next.js production build pass on the current `main` branch.

## Design Decisions and Assumptions

### Major Design Decisions

- The application uses a separated frontend and backend architecture. Next.js provides the user interface, while FastAPI exposes a REST API.
- PostgreSQL is used for persistent relational data, with SQLAlchemy providing database access.
- Alembic manages database schema migrations so database changes remain reproducible.
- JWT access tokens provide stateless authentication between the frontend and backend.
- Argon2 is used for secure password hashing.
- Role-based authorization protects administrative and managerial operations.
- Companies act as parent records for related contacts and leads.
- Lead filtering and sorting are performed by the backend to keep queries efficient and reusable.
- CSV imports include a preview and validation step before records are written to the database.
- A separate PostgreSQL database is used for automated tests.

### Assumptions

- Each contact belongs to one company.
- Each lead belongs to one company and may optionally reference a contact from that company.
- Leads use the stages New, Contacted, Qualified, Won, and Lost.
- Authorized users can view CRM information, while privileged operations depend on their assigned role.
- The frontend and backend run as separate services.
- Local frontend development uses port 3000, and the backend uses port 8000.
- Production deployments must provide secure environment variables and trusted CORS origins.

## Security Notes

* Never commit `backend/.env` or `frontend/.env.local`.
* Use a long, randomly generated JWT secret.
* Keep development and test databases separate.
* Restrict `CORS_ORIGINS` to trusted frontend domains in production.
* Use HTTPS and secure secret management in production.
* Apply Alembic migrations before starting a newly deployed backend.

## Repository

GitHub: [areeba-munir/mini-crm](https://github.com/areeba-munir/mini-crm)
