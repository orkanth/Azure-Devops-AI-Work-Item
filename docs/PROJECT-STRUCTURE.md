# Project structure and responsibilities

## Top-level layout

- `apps/web`: Angular user interface. Feature areas are generator, review, and publish; `core` contains app-wide services/interceptors/auth; `shared` contains reusable UI and models.
- `apps/api`: NestJS application API. Owns request validation, authentication/authorization, generation sessions, document metadata, approvals, and API coordination.
- `services/ai-service`: FastAPI AI service. Owns document extraction, chunking, embeddings/retrieval, LLM calls, structured work-item generation, and the LangGraph workflow.
- `services/azure-devops-mcp`: FastMCP server. Exposes a small, validated set of tools that call Azure DevOps APIs.
- `packages/contracts`: JSON schemas and examples that document request/response shapes shared between services.
- `infra`: local container configuration and infrastructure scripts.
- `docs`: architecture diagrams, decisions (ADRs), API notes and setup guides.
- `tests/e2e`: end-to-end scenarios spanning the UI, APIs and Azure DevOps integration.

## Service boundaries

### Angular (`apps/web`)

Calls the NestJS API only. It should never contain the LLM key, Chroma credentials, or Azure DevOps PAT. The main wizard pages are Generate, Review, and Publish.

### NestJS (`apps/api`)

Owns app-facing REST endpoints, authorization, request validation, approval records and coordination with the AI service. Keep secrets and all write authorization on the server side.

### AI service (`services/ai-service`)

Suggested graph stages: `parse_input -> retrieve_context (when useful) -> generate_hierarchy -> validate_hierarchy -> check_duplicates -> await_approval -> publish`. The publish stage should be gated by a verifiable approval from the application API; it should not execute merely because a model asks it to.

### Azure DevOps MCP server (`services/azure-devops-mcp`)

Start read-only with project/team/iteration discovery, supported work-item types, work-item search, and user identity search. Then add `create_work_item`, `update_work_item`, `delete_work_item`, `assign_work_item`, and `link_work_items`. All writes must independently enforce authorization and validation; deletes require explicit confirmation tied to the exact target IDs. See `FUNCTIONAL-REQUIREMENTS.md`.

### ChromaDB / RAG

Use ChromaDB for vector storage and retrieval of document chunks; store source document IDs, page/section metadata, and chunk IDs as metadata. The original uploaded document and application-generation state are not the vector database's responsibility.

## Initial implementation order

1. Azure DevOps organization/project and a manual test work item.
2. Read-only FastMCP server and client connectivity.
3. LLM-backed prompt-to-structured-hierarchy endpoint with schema validation.
4. DOCX/PDF ingestion and ChromaDB retrieval.
5. LangGraph validation, duplicate detection and approval gates.
6. Angular Generate/Review/Publish UI.
7. End-to-end test for parent/child links, iteration paths, retries, and partial failures.
