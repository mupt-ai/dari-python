# dari-python

`dari-python` is a tiny, well-typed wrapper around the [Dari workflow automation API](https://docs.usedari.com). It exposes the handful of public endpoints documented in `docs/` (start workflows, list executions, resume paused runs, manage credentials, and kick off single computer-use actions) through a single `Dari` client.

## Features

- Minimal dependency footprint (just `requests`)
- Friendly `Dari` client that stores your API key and handles headers/JSON boilerplate
- Helpers for workflow lifecycle methods: start, list executions, inspect execution details
- Convenience methods for credential metadata, OAuth accounts, webhooks, and single-action runs
- Context-manager support plus consistent error handling via `DariError`

## Installation

```bash
pip install dari-python
```

## Quickstart

```python
from dari import Dari

client = Dari(api_key="YOUR_API_KEY")

# 1. Start a workflow
start = client.start_workflow(
    workflow_id="23a45a3f-c58c-492a-8e81-0fe6b3704ad2",
    input_variables={"primary_email": "avyay@mupt.ai"},
)
print("Execution ID:", start["workflow_execution_id"])

# 2. List executions for the workflow
executions = client.list_workflow_executions("23a45a3f-c58c-492a-8e81-0fe6b3704ad2")
print("Total executions:", len(executions["executions"]))

# 3. Poll execution details
execution = client.get_execution_details(
    workflow_id="23a45a3f-c58c-492a-8e81-0fe6b3704ad2",
    execution_id=start["workflow_execution_id"],
)
print("Execution status:", execution["status"])

# 4. Resume a paused workflow inside your webhook handler
# resume_payload = client.resume_workflow(resume_url, {"user_response": "approved"})

# 5. Manage credentials
credential = client.create_credential(
    service_name="Gmail",
    username_or_email="user@example.com",
    password="mypassword",
    totp_secret="JBSWY3DPEHPK3PXP",
)
print("Created credential:", credential["id"])

# 6. Manage phone numbers for SMS 2FA
phone_number = client.purchase_phone_number(label="Support Line")
print("Purchased phone:", phone_number["phone_e164"])

phone_numbers = client.list_phone_numbers()
print(f"Total phone numbers: {len(phone_numbers)}")

# 7. Trigger a single computer-use action
client.run_single_action(
    cdp_url="ws://localhost:9222/devtools/page/123",
    action="Open Google Calendar and create a meeting",
    identifier="calendar-meeting-step",
    variables={"meeting_title": "Internal sync"},
)
```

## API Coverage

Each method maps one-to-one with the docs under `docs/api-reference/endpoint/`:

| Client method | HTTP call |
| --- | --- |
| `start_workflow(workflow_id, input_variables)` | `POST /workflows/start/{workflow_id}` |
| `list_workflow_executions(workflow_id)` | `GET /public/workflows/{workflow_id}` |
| `get_execution_details(workflow_id, execution_id)` | `GET /public/workflows/{workflow_id}/executions/{execution_id}` |
| `resume_workflow(resume_url, variables)` | `POST {resume_workflow_url}` |
| `list_credentials()` | `GET /credentials` |
| `create_credential(**kwargs)` | `POST /credentials` |
| `list_connected_accounts()` | `GET /connected-accounts` |
| `list_phone_numbers()` | `GET /phone-numbers` |
| `purchase_phone_number(label)` | `POST /phone-numbers` |
| `run_single_action(**kwargs)` | `POST /single-actions/run-action` |

## Error handling

- Network or HTTP failures raise `dari.DariError`
- `DariError.status_code` exposes the HTTP code when available
- The raw `requests.Response` object is attached to `DariError.response` for advanced debugging

## Development

Standard Python packaging layout is used (`src/` tree + `pyproject.toml`). A simple sanity check before publishing:

```bash
pip install -e .
python -m compileall src/dari
```

Contributions are welcome via pull request.
