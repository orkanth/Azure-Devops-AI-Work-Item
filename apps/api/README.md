# NestJS Application API

The NestJS app is configured at the repository root. Run `npm run start:api` from the repository root. The starter health endpoint is `GET /api/health`.

Responsibilities: app-facing REST endpoints, auth/authorization, DTO validation, generation sessions, document metadata, approval records, and orchestration between the web app and AI service.

Planned modules:
- `health`: liveness/readiness endpoints
- `generation`: start generation and fetch proposals
- `documents`: upload metadata and ingestion status
- `approvals`: record explicit approval of a proposal version
- `azure-devops`: project/team/iteration lookup via the MCP integration boundary
- `auth` and `users`: identity integration and access control

Use DTO validation and authorization guards. Do not place Azure DevOps credentials or LLM keys in frontend configuration.
