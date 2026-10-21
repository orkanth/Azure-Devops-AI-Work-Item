# Angular Web App

The Angular 20 frontend currently includes an interactive UI prototype for the Azure DevOps AI Work Item Generator.

## Screens
- **AI command center:** prompt-driven create, update, assign and delete proposal preview, summary cards and recent work items.
- **Work items:** filter/search items, edit work-item fields, prepare delete confirmations and inspect parent relationships.
- **Documents & RAG:** select PDF/DOCX files and view the planned document-ingestion pipeline.
- **Integrations:** connection-status placeholders for Azure DevOps, FastMCP, an LLM provider and ChromaDB.

## Run
From the repository root:

```bash
npm install
npm run start:web
```

Then open `http://localhost:4200`.

## Prototype limitation
The current frontend uses `MockWorkItemService` and in-memory sample data. Prompt interpretation is a lightweight rule-based preview to demonstrate interactions; it is not an LLM and changes do not persist after refresh. File selection does not upload or parse a document. Azure DevOps, NestJS, FastAPI, ChromaDB, LangGraph and FastMCP still need to be implemented and connected. Never place Azure credentials in Angular.

## Prompt examples
- `Create a user story for password reset`
- `Assign task #104 to Alex Morgan`
- `Move API validation to Done`
- `Delete task #106`
- `Rename #104 to Validate the login request payload`
