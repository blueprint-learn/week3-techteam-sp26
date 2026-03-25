# Week 3 Tech Team Workshop — Intro to PostgreSQL

## Assignment overview

You will:

1. Define two related tables (`resources` and `referrals`) with keys and constraints.
2. Insert carefully specified seed data.
3. Write seven small SQL queries that practice filtering, joining, and aggregation.

Your work is checked by **automated tests** (`pytest`) that connect to your local database, load your SQL files, and verify schemas, constraints, data, and query outputs.

## Prerequisites

- **Docker Desktop** (or another Docker engine) installed and running
- **Python 3.10+**
- Basic programming comfort (variables, functions). No prior SQL required.

## Setup

### 1) Clone your assignment repository

Use the link from **GitHub Classroom** (your personal copy of this starter repo).

### 2) Create a virtual environment (recommended)

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 3) Configure environment variables

Copy the example env file and keep the defaults unless your instructor tells you otherwise:

**macOS / Linux**

```bash
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

The tests read `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` from `.env` (via `python-dotenv`).

## Run PostgreSQL with Docker

From the repository root:

```bash
docker compose up -d
```

Checks:

- **List containers** (should show `week3-postgres-workshop` healthy / running):
  ```bash
  docker ps
  ```
- **Optional: follow logs** while debugging:
  ```bash
  docker compose logs -f db
  ```

Stop the database when you are done for the day:

```bash
docker compose down
```

> If port `5432` is already used on your machine, change `POSTGRES_PORT` in **both** `.env` and `docker-compose.yml`’s host port mapping (or stop the other Postgres instance).

## Complete the SQL tasks (student work)

### Task 1 — Schema (`schema/01_create_tables.sql`)

Create:

- `**resources`**: `id`, `name` (**NOT NULL**), `category`, `address`, `contact_email`
- `**referrals`**: `id`, `family_name` (**NOT NULL**), `resource_id` (**foreign key → `resources.id`**), `referral_date`, `notes`

Hints:

- Use `SERIAL` (or `GENERATED ... AS IDENTITY`) for integer primary keys.
- Create `resources` first, then `referrals`.

### Task 2 — Seed data (`schema/02_seed_data.sql`)

Insert the exact rows listed in the comments of `schema/02_seed_data.sql`:

- **5 resources** and **6 referrals**
- Use the **explicit ids** shown (so tests are deterministic).
- Include multiple categories, multiple referrals for the same resource, and one resource with **zero** referrals.

### Tasks 3–7 — Queries (`student_queries/`)

Edit each file so the **final SQL statement** is a `SELECT` that meets the comment requirements:


| File                                   | What it should do                                                                                                                                                       |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_get_all_resources.sql`             | All columns from `resources`, ordered by `id`                                                                                                                           |
| `02_filter_food_resources.sql`         | Only `category = 'Food'`, ordered by `id`                                                                                                                               |
| `03_search_name.sql`                   | Case-insensitive match for “pantry” in `name`; columns `id`, `name`, `category`                                                                                         |
| `04_referrals_with_resource_names.sql` | `JOIN` referrals to resources; columns `**family_name`**, `**resource_name**` (exact aliases), ordered by `referrals.id`                                                |
| `05_count_referrals_per_resource.sql`  | Every resource with referral counts (**include zeros**); columns `**resource_id`**, `**resource_name**`, `**referral_count**` (exact aliases), ordered by `resource_id` |


You can run statements manually with `psql` if you like, but **pytest is the grader**.

## Run tests locally

Ensure Docker is up and `.env` exists, then:

```bash
pytest -q
```

What the tests do (high level):

- Connect using your `.env` settings
- **Reset** relevant tables between checks (deterministic runs)
- Execute `schema/01_create_tables.sql` then `schema/02_seed_data.sql`
- Verify **foreign keys**, **NOT NULL**, seed **row values**, and each **query output**

If something fails, read the assertion message: it usually names the SQL file to fix and what mismatched.

## Submission expectations

Follow your instructor’s GitHub Classroom deadline and submission steps. Typically you will:

1. Commit your completed `.sql` files (only in `schema/` and `student_queries/`).
2. Push to your assignment branch / `main` on your personal repo.
3. Confirm **Green checks** if Classroom autograding is enabled (or attach test output if asked).

**Do not commit secrets.** `.env` is gitignored; use `.env.example` as the template only.

## Troubleshooting


| Symptom                                    | What to try                                                             |
| ------------------------------------------ | ----------------------------------------------------------------------- |
| `could not connect` / `Connection refused` | `docker compose up -d`, wait ~10s, retry `pytest -q`                    |
| Auth errors                                | Ensure `.env` matches the username/password/db in `docker-compose.yml`  |
| Port conflict on 5432                      | Change the **host** port mapping and `POSTGRES_PORT` in `.env` together |
| Tests say SQL file is empty                | Replace `# TODO` placeholders with real statements                      |


## For instructors (GitHub Classroom notes)

- Starter files intentionally contain **TODOs only** — no solutions in `schema/` or `student_queries/`.
- This repo is designed to work with a simple **pytest** autograder that provision Docker (or uses a service container) before `pytest -q`.
- Lecture alignment: durable storage vs in-memory dicts; relational vs non-relational; PostgreSQL as an RDBMS; `CREATE TABLE` / `INSERT` / `SELECT` / `JOIN` / one-to-many relationships.

---

**Questions?** Ask in your tech team workshop channel or during office hours.