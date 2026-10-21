# Angular UI prototype

## What is included

The `apps/web` application now contains an interactive prototype for the three main work-management steps, plus supporting navigation pages:

1. **AI command center** — prompt input, starter prompts, action preview, approval/apply button, summary statistics and recent work items.
2. **Work items** — search and filters, parent/child display, edit form, and a delete confirmation step.
3. **Documents & RAG** — choose a `.docx` or `.pdf` file and review the intended extraction, embedding and retrieval pipeline.
4. **Integrations** — placeholder statuses for Azure DevOps, FastMCP, the LLM provider and ChromaDB.

## Prompts to try

- `Create a user story for password reset`
- `Create an Epic called User Management`
- `Assign task #104 to Alex Morgan`
- `Assign API input validation task to Alex Morgan`
- `Move API validation to Done`
- `Edit task #104 state to Active`
- `Rename #104 to Validate the login request payload`
- `Delete task #106`

When targeting an existing item, including the Azure DevOps work-item ID (e.g. `#104`) is the clearest option. If a title-only command has multiple equally good matches, the UI offers a selection instead of silently picking one. Delete requires a separate checkbox confirmation.

## Important current limitations

- The prompt interpreter is a small rule-based demonstration, not a connected LLM or LangGraph workflow.
- Changes operate on in-memory sample data and are discarded on page refresh.
- Assignment accepts free text in the prototype; the live backend must resolve the person against Azure DevOps identities and ask the user to choose when multiple identities match.
- The document control selects the file in the browser but does not upload or parse it.
- Azure DevOps, NestJS endpoints, FastAPI, ChromaDB, LangGraph and FastMCP are not yet connected.
- The UI's state names are demo states. The live integration must read state values available for the project's configured Azure DevOps process and map user phrases such as "Done" to a valid state.

## Run locally

From the repository root:

```bash
npm install
npm run start:web
```

Open `http://localhost:4200`.
