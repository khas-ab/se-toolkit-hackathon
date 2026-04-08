# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

<!-- Paste the agent's response to "What is the agentic loop?" and "What labs are available in our LMS?" -->

## Task 1B — Agent with LMS tools

<!-- Paste the agent's response to "What labs are available?" and "Describe the architecture of the LMS system" -->

## Task 1C — Skill prompt

<!-- Paste the agent's response to "Show me the scores" (without specifying a lab) -->

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

**Happy path (status 200):**

```
2026-03-30 16:53:54,216 INFO [app.main] [main.py:60] [trace_id=8c0e77d2a1c07aa62ff5f8cb2d4024ef span_id=86a69bc792799c29 resource.service.name=Learning Management Service trace_sampled=True] - request_started
2026-03-30 16:53:54,726 INFO [app.auth] [auth.py:30] [trace_id=8c0e77d2a1c07aa62ff5f8cb2d4024ef span_id=86a69bc792799c29 resource.service.name=Learning Management Service trace_sampled=True] - auth_success
2026-03-30 16:53:54,895 INFO [app.db.items] [items.py:16] [trace_id=8c0e77d2a1c07aa62ff5f8cb2d4024ef span_id=86a69bc792799c29 resource.service.name=Learning Management Service trace_sampled=True] - db_query
2026-03-30 16:53:56,885 INFO [app.main] [main.py:68] [trace_id=8c0e77d2a1c07aa62ff5f8cb2d4024ef span_id=86a69bc792799c29 resource.service.name=Learning Management Service trace_sampled=True] - request_completed
```

**Error path (db_query failure):**

```
2026-03-30 16:55:22,564 INFO [app.db.items] [items.py:16] [trace_id=fe1a5de6b185174a839c0998ef8cc22b span_id=04950f8ebca82d78 resource.service.name=Learning Management Service trace_sampled=True] - db_query
2026-03-30 16:55:22,616 ERROR [app.db.items] [items.py:20] [trace_id=fe1a5de6b185174a839c0998ef8cc22b span_id=04950f8ebca82d78 resource.service.name=Learning Management Service trace_sampled=True] - db_query
```

**VictoriaLogs query:**

Query: `severity:ERROR`

Sample error log output:

```json
{
  "_time": "2026-03-30T17:26:45.799958784Z",
  "severity": "ERROR",
  "event": "db_query",
  "error": "[Errno -2] Name or service not known",
  "service.name": "Learning Management Service",
  "trace_id": "c9488b6fa689fe8443ccfd943456691a",
  "span_id": "52463ffd7186d5de"
}
```

**Screenshot:** Open `http://localhost:42002/utils/victorialogs/select/vmui`, run query `severity:ERROR`, and paste screenshot here.

## Task 3B — Traces

**Healthy trace example:**

- Trace ID: `2578212b8b7a5c7d0c9fdbb37390086c`
- Operation: `GET /docs`
- Status: 200 OK
- Spans: request_started → request_completed

**Error trace example:**

- Trace ID: `c9488b6fa689fe8443ccfd943456691a`
- Operation: `GET /items/`
- Status: 404 (db_query failed)
- Error: `[Errno -2] Name or service not known`
- Spans: request_started → auth_success → db_query (ERROR) → request_completed

**Screenshots:**

1. Open `http://localhost:42002/utils/victoriatraces/select/vmui`
2. Search for "Learning Management Service"
3. Find trace `c9488b6fa689fe8443ccfd943456691a` showing the db_query error
4. Paste screenshots of both healthy and error traces here

## Task 3C — Observability MCP tools

**MCP Tools Implemented:**

The following observability tools are registered in the nanobot:

- `logs_search` — Search logs using VictoriaLogs LogsQL queries
- `logs_error_count` — Count errors per service over a time window
- `traces_list` — List recent traces for a service
- `traces_get` — Fetch a specific trace by ID

**Verification:**

Nanobot logs confirm the MCP server is connected:

```
MCP server 'observability': connected, 4 tools registered
```

VictoriaLogs API tested directly:

```bash
curl "http://localhost:42010/select/logsql/query?query=severity:ERROR&limit=5"
```

Returns error logs with trace IDs for correlation.

VictoriaTraces API tested directly:

```bash
curl "http://localhost:42011/select/jaeger/api/traces?service=Learning%20Management%20Service&limit=3"
```

Returns traces with full span hierarchy including error details.

**Agent responses:**

**To test the agent:**

1. Open the Flutter web app at `http://localhost:42002`
2. Start a new chat
3. Ask: **"Any errors in the last hour?"**
4. Paste the agent's response below

**Normal conditions response:**

<!-- Paste agent response here -->

**Error conditions response (after stopping postgres):**

<!-- Stop postgres: docker compose --env-file .env.docker.secret stop postgres -->
<!-- Trigger a request, then ask the agent again -->
<!-- Paste agent response here -->
<!-- Restart postgres: docker compose --env-file .env.docker.secret start postgres -->

## Task 4A — Multi-step investigation

**Investigation performed (with PostgreSQL stopped):**

### Step 1: Search for recent errors

```
Query: severity:ERROR
Found multiple db_query errors with:
  - Error: "[Errno -2] Name or service not known"
  - Service: Learning Management Service
  - Trace ID: 1e11924a15eee7257c3ddd3bf2e77b0a
```

### Step 2: Fetch the trace

```
Trace ID: 1e11924a15eee7257c3ddd3bf2e77b0a
Spans: 5
  - GET /items/ http send - OK
  - GET /items/ http send - OK
  - GET /items/ http send - OK
  - connect - ERROR ([Errno -2] Name or service not known)
  - GET /items/ - OK
```

**Agent's expected response:**

> "I found a failure in the Learning Management Service. The `connect` operation (database connection) failed with error `[Errno -2] Name or service not known` — the database is unreachable. This occurred during a `GET /items/` request. Trace ID: `1e11924a15eee7257c3ddd3bf2e77b0a`"

**Note:** The LLM service is currently experiencing external API issues. To verify the agent response:

1. Ensure the LLM service is healthy
2. Open the Flutter app at `http://localhost:42002`
3. Ask: "What went wrong?"
4. Paste the actual agent response here

## Task 4B — Proactive health check

**To complete this section:**

1. In the Flutter chat, ask the agent:

   > "Create a health check for this chat that runs every 2 minutes. Each run should check for backend errors in the last 2 minutes, inspect a trace if needed, and post a short summary here. If there are no recent errors, say the system looks healthy. Use your cron tool."

2. Ask: "List scheduled jobs."

3. Trigger another failure (with postgres still stopped):

   ```bash
   curl -s "http://localhost:42001/items/" -H "Authorization: Bearer secret-key"
   ```

4. Wait for the cron job to run and post a health report

5. Paste the proactive health report here:

<!-- Paste proactive health report transcript here -->

1. Ask the agent to remove the test job

2. Restart PostgreSQL:

   ```bash
   docker compose --env-file .env.docker.secret start postgres
   ```

## Task 4C — Bug fix and recovery

**Root cause analysis:**

The planted bug was in `backend/app/routers/items.py`, in the `get_items` endpoint. When any exception occurred (including database connection errors), it returned HTTP 404 "Items not found" instead of HTTP 500 "Internal Server Error". This masked the real failure — when PostgreSQL is stopped, the error should be "database unreachable" (500), not "items not found" (404).

**Fix applied:**

Changed the exception handler in `backend/app/routers/items.py` line 21-25:

```diff
 @router.get("/", response_model=list[ItemRecord])
 async def get_items(session: AsyncSession = Depends(get_session)):
     """Get all items."""
     try:
         return await read_items(session)
     except Exception as exc:
-        raise HTTPException(
-            status_code=status.HTTP_404_NOT_FOUND,
-            detail="Items not found",
-        ) from exc
+        # Database errors (connection refused, etc.) should return 500
+        # Only return 404 if items genuinely don't exist (empty list from DB)
+        raise HTTPException(
+            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
+            detail=f"Database error: {str(exc)}",
+        ) from exc
```

**Post-fix verification:**

1. Redeploy: `docker compose --env-file .env.docker.secret up --build -d`
2. Stop PostgreSQL and trigger a request
3. Ask "What went wrong?" — should show the real underlying failure
4. Restart PostgreSQL
5. Create a new health check and verify it reports healthy

<!-- Paste post-fix agent response and healthy report here -->
