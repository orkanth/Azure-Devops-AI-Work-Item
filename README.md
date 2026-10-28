# Azure DevOps AI Work Item Generator

An AI-assisted application that turns natural-language prompts and technical design documents into a reviewable hierarchy of Azure DevOps work items. The user reviews and explicitly approves the proposed items before the application creates them in Azure DevOps.

## Planned stack

- **Frontend:** Angular 20, TypeScript, Signals, PrimeNG, Tailwind CSS
- **Application API:** NestJS
- **AI service:** Python, FastAPI, LangChain, LangGraph, an LLM provider
- **RAG:** document extraction/chunking, embeddings, ChromaDB, LangChain retrievers
- **Tool integration:** FastMCP server plus an MCP client
- **Work-item platform:** Azure DevOps REST API
- **Application metadata:** PostgreSQL

## Repository layout

```text
apps/                  Angular UI and NestJS API
services/               Python AI service and Azure DevOps MCP server
packages/contracts/     JSON schemas and cross-service examples
infra/                  Docker and local development infrastructure
docs/                   Architecture, setup guides, API notes and ADRs
scripts/                Developer helper scripts
tests/e2e/              End-to-end test scenarios
```

## User workflow

1. Enter a prompt or upload a DOCX/PDF technical document.
2. Extract and optionally index the document chunks in ChromaDB.
3. Generate Epics, Features, User Stories and Tasks with the LLM.
4. Validate the hierarchy and let the user review/edit it.
5. Require explicit approval before write operations.
6. Use the MCP tools and Azure DevOps REST API to create and link approved work items.
7. Return created work-item IDs and links, including per-item failures.

## Package management

- The root [`package.json`](package.json) manages the shared Node.js dependencies and scripts for Angular and NestJS. Install Node dependencies once from the repository root with `npm install`.
- Python services are managed separately using each service's `pyproject.toml` (recommended tool: `uv`). They do not use `package.json`.
- `angular.json` and `nest-cli.json` configure the frontend and API projects.

## Current implementation status

- **Angular frontend:** interactive prototype with AI command center, work-item table, edit dialog, command preview, delete confirmation, document/RAG page and integration-status page.
- **Prompt parser:** lightweight rule-based local preview for common create, update, assign and delete commands. It is not an LLM.
- **Mock data:** work-item operations update in-memory sample data only; changes disappear after refresh.
- **Not connected yet:** Azure DevOps REST API, NestJS API endpoints, LLM provider, LangGraph workflow, document extraction, ChromaDB and FastMCP tools.

Never commit real API keys, Azure DevOps PATs, connection strings or uploaded documents. See [`docs/FUNCTIONAL-REQUIREMENTS.md`](docs/FUNCTIONAL-REQUIREMENTS.md) for the intended live behaviour and safeguards.

## Run the Angular UI

From the repository root, with a compatible Node.js version installed:

```bash
npm install
npm run start:web
```

Then open `http://localhost:4200`.

## Try these prompt examples

- `Create a user story for password reset`
- `Assign task #104 to Alex Morgan`
- `Move API validation to Done`
- `Rename #104 to Validate the login request payload`
- `Delete task #106` — displays a separate confirmation checkbox before changing the local demo data.

Updates and deletes resolve the target by ID when an ID is supplied. If a title matches multiple items, the UI asks you to select the exact item. For the live implementation, the backend must revalidate target IDs and user identity, and execute writes only after the appropriate approval.


######Create Nestjs Service, Contoller, Modules#########
npx nx g @nx/nest:service apps/api/src/app/modules/health/health.service.ts
npx nx g @nx/nest:module apps/api/src/app/modules/health/health.module.
npx nx g @nx/nest:controller apps/api/src/app/modules/health/health.controller.ts --module=apps/api/src/app/modules/health/health.module.ts