# Azure DevOps FastMCP Server

Expose narrow, typed tools for the Azure DevOps REST API. Start read-only. Add write tools only after auth and approval tests pass.

Suggested tool groups:
- Read: `list_projects`, `list_teams`, `list_iterations`, `get_work_item_types`, `search_work_items`, `get_work_item`
- Write (later): `create_work_item`, `link_work_items`, `update_work_item`, `assign_work_item`, `set_iteration_path`

Validate every input; restrict organization/project scope; keep credentials in environment variables or a secret manager; redact secrets from logs. Work-item types vary by the project's process, so query them rather than assuming a fixed hierarchy.
