# SPMS — B2B 業務與專案管理系統 (GEMINI Context)

## Project Overview

SPMS (Sales & Project Management System) is a Python-based web application designed as an internal tool for B2B sales and project management teams. It provides a unified platform to manage the entire lifecycle from presale lead development to postsale project execution.

The architecture follows a clear separation of concerns between the presentation layer and the business logic/data layer.

*   **Frontend**: The UI is built entirely with **Streamlit**. Each feature or view is a separate Python file in the `pages/` directory.
*   **Backend**: The business logic resides in the `services/` directory. It uses **Python** and communicates with the database using raw SQL queries via the **`psycopg2`** library. **No ORM is used**.
*   **Database**: The application is backed by a **PostgreSQL 16** database, which is managed via Docker. The complete database schema, including idempotent migration scripts, is defined in `database/schema.sql`.

Key functionalities include presale pipeline management (state machine from L0 to L7), postsale project tracking (tasks, Gantt charts), a normalized Customer Relationship Management (CRM) system, sales forecasting, and a client health scoring mechanism.

## Building and Running

The project uses Docker for the database and `pip` for Python dependencies. The `README.md` provides a clear quick-start guide.

1.  **Start PostgreSQL Database:**
    *   This command starts the PostgreSQL container in the background. The database will be available on `localhost:5433`.

    ```bash
    docker-compose up -d
    ```

2.  **Install Python Dependencies:**
    *   This installs all required Python libraries, such as Streamlit and psycopg2.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize the Database:**
    *   This Python command executes the `database/schema.sql` script. The script is idempotent, meaning it can be run safely multiple times. It will create all necessary tables and apply any required alterations if they don't already exist.

    ```bash
    python -c "from database.connection import init_db; init_db()"
    ```

4.  **Load Seed Data (Optional):**
    *   To populate the application with sample data for testing.

    ```bash
    python database/seed.py
    ```

5.  **Run the Application:**
    *   This command starts the Streamlit web server.

    ```bash
    streamlit run app.py
    ```

## Development Conventions

*   **Separation of Layers**:
    *   **`pages/`**: Contains only UI/presentation logic (Streamlit components). It should **never** contain SQL queries. It calls service functions to get data or perform actions.
    *   **`services/`**: Contains all business logic and database interactions. All SQL queries are encapsulated here. Functions in this layer take simple Python types and return data, typically as lists of dictionaries.

*   **Database Interaction**:
    *   **No ORM**: All database operations are performed using raw SQL queries with the `psycopg2` library.
    *   **Connection Pooling**: All services must get a database connection using the `get_connection()` context manager from `database/connection.py`. This ensures connections are managed correctly.
    *   **Idempotent Schema**: The single source of truth for the database schema is `database/schema.sql`. Any changes to the database structure (e.g., adding a column) should be done by adding an idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` statement to the bottom of this file. The `init_db()` function handles the migration automatically on startup.

*   **State Management & Business Rules**:
    *   Core business constants, status codes, state machine transition rules (`PRESALE_TRANSITIONS`), and logic weights (e.g., `HEALTH_SCORE_WEIGHTS`) are centralized in `constants.py`. This is the primary file to consult for business logic rules.

*   **Sprint-Based Workflow**:
    *   Development follows a highly structured, five-stage sprint process as defined in `docs/SPRINT_GUIDE.md`. Each sprint involves planning (defining User Stories and DoD), coding, reviewing, and refactoring, with progress tracked in the corresponding `docs/sprints/SXX.md` file.
