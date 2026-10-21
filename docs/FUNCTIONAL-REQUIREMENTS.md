# Functional requirements: prompt-driven Azure DevOps work-item management

## Goal

A user can manage Azure DevOps Epics, Features, User Stories (or Product Backlog Items, depending on the project's process), and Tasks using natural-language prompts. Changes must be applied to Azure DevOps itself, not only to local application data.

## Supported prompt operations

### Create

- Create one or more Epics, Features, User Stories/Product Backlog Items, and Tasks.
- Create parent-child relationships in the right hierarchy.
- Support assignee, description, acceptance criteria, priority, estimate, area path, and iteration path when compatible with the selected process and item type.
- Return the created IDs and direct Azure DevOps links.

Example: `Create an Epic called User Management, add a Login Feature, create a user story for email/password login, and assign the login API task to Alex Morgan.`

### Read and resolve

- Search existing work items by ID, title, type, project, state, parent, or assignee.
- Before update or delete, resolve the prompt to a specific work-item ID and show the ID, title, and type.
- If more than one item matches, do not choose the first result silently. Ask the user to select the intended item.

### Update

- Update title, description, acceptance criteria, state, priority, estimate, parent link, assignee, area path, or iteration path when the selected work-item type supports the field.
- Show a concise change summary before applying meaningful or ambiguous changes.
- Re-check the selected item immediately before the write to reduce the risk of updating a stale or incorrect record.

Example: `Move the Login API task to In Progress and assign it to Alex Morgan.`

### Assign / reassign

- Resolve a requested person by exact email or uniquely matching display name using Azure DevOps identity/user APIs.
- If a name matches multiple identities, ask the user to choose. Never guess an identity.
- Verify that the resolved identity is valid for the organization/project and that the caller has permission to assign the item.
- Return the selected assignee and the updated work-item ID.

Example: `Assign task 482 to alex.morgan@example.com.`

### Delete

- Treat deletion as a destructive action. First identify the exact IDs, titles and item types that would be deleted.
- Require explicit confirmation before executing a deletion. A request to delete a broad set, such as all tasks, requires a preview of the full scope and a separate confirmation.
- Do not silently expand a deletion to child items. Explain whether child items or links are affected and follow Azure DevOps API behavior.
- Log the requesting user, confirmed operation, target IDs, result, and any failures.

Example: `Delete task 482.` The system must show `Task 482 — Create login API` and ask for confirmation before deleting it.

## AI workflow

1. Parse the prompt and classify the requested operation(s).
2. Identify the Azure DevOps organization, project and team context.
3. Discover the project's supported work-item types and fields.
4. Search and resolve target items/users when an operation refers to existing data.
5. Ask a clarification question if the target or intent is ambiguous.
6. Validate the proposed operation against schemas, permissions and business rules.
7. Show a review/confirmation step for writes; require explicit confirmation for all deletes and bulk operations.
8. Execute through the FastMCP server using Azure DevOps REST APIs.
9. Verify results and return IDs, links, successes, failures and retry guidance.

## Initial MCP tool inventory

Read tools: `list_projects`, `list_teams`, `list_iterations`, `get_work_item_types`, `search_work_items`, `get_work_item`, `search_users`, `get_work_item_fields`.

Write tools: `create_work_item`, `update_work_item`, `delete_work_item`, `assign_work_item`, `link_work_items`, `set_iteration_path`.

The model must not be allowed to bypass authorization or confirmation gates by calling a tool directly. The service must independently enforce permissions, validation, target resolution, and approval requirements.

## Acceptance criteria

- A natural-language prompt can create supported work items and parent-child links in a test Azure DevOps project.
- A prompt can update an existing item only after the system resolves the intended ID.
- An ambiguous title or person name triggers clarification rather than a guessed write.
- Assignments use a resolved Azure DevOps identity, not an unverified free-text name.
- Deletes cannot execute without explicit confirmation tied to the exact displayed target IDs.
- Bulk operations show the affected item count and full target list before confirmation.
- The response includes per-item IDs, links, status and errors, including partial-failure cases.
- Tests cover create, update, assign, delete confirmation, ambiguous matches, permission failures, duplicate requests and API failures.
