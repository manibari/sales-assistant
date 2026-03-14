Check Supabase PostgreSQL connection health, latency, and data summary.

Steps:

1. Run a Python script that does the following (use `python -c`):
   - Load `.env` via dotenv
   - Connect to `DATABASE_URL` via psycopg2
   - Measure connection time
   - Run `SELECT version()` and print PostgreSQL version
   - Measure query latency with `SELECT 1`
   - Count rows in key tables: `nx_client`, `nx_partner`, `nx_contact`, `nx_intel`, `nx_deal`, `nx_meeting`, `nx_subsidy`, `nx_tbd_item`, `nx_document`, `nx_file`
   - Check connection pool status if available

2. Report results as a table:

| Metric | Value |
|--------|-------|
| PostgreSQL version | ... |
| Connection latency | ...ms |
| Query latency | ...ms |
| Pool status | active / not initialized |

| Table | Rows |
|-------|------|
| nx_client | ... |
| nx_deal | ... |
| ... | ... |

3. If connection fails, show the error and suggest checking:
   - `DATABASE_URL` in `.env`
   - Network connectivity to Supabase
   - Supabase project status (paused?)
