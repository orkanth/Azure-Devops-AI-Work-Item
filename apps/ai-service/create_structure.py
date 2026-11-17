
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "app"

files = [
    "main.py",

    # API
    "api/__init__.py",
    "api/dependencies.py",
    "api/routes/__init__.py",
    "api/routes/root.py",
    "api/routes/health.py",
    "api/routes/chat.py",
    "api/routes/work_items.py",
    "api/routes/documents.py",
    "api/routes/integrations.py",

    # Core
    "core/__init__.py",
    "core/config.py",
    "core/logging.py",
    "core/exceptions.py",
    "core/security.py",

    # Agents
    "agents/__init__.py",
    "agents/supervisor/__init__.py",
    "agents/supervisor/agent.py",
    "agents/supervisor/prompts.py",
    "agents/work_items/__init__.py",
    "agents/work_items/agent.py",
    "agents/work_items/prompts.py",
    "agents/users/__init__.py",
    "agents/users/agent.py",
    "agents/users/prompts.py",
    "agents/rag/__init__.py",
    "agents/rag/agent.py",
    "agents/rag/prompts.py",
    "agents/generation/__init__.py",
    "agents/generation/agent.py",
    "agents/generation/prompts.py",

    # Tools
    "tools/__init__.py",
    "tools/registry.py",
    "tools/common/__init__.py",
    "tools/common/date_tools.py",
    "tools/common/calculator_tools.py",
    "tools/azure_devops/__init__.py",
    "tools/azure_devops/work_item_tools.py",
    "tools/azure_devops/user_tools.py",
    "tools/azure_devops/project_tools.py",
    "tools/rag/__init__.py",
    "tools/rag/knowledge_tools.py",
    "tools/documents/__init__.py",
    "tools/documents/document_tools.py",

    # LangGraph
    "graph/__init__.py",
    "graph/state.py",
    "graph/nodes.py",
    "graph/edges.py",
    "graph/workflow.py",
    "graph/checkpoint.py",

    # Services
    "services/__init__.py",
    "services/llm_service.py",
    "services/nestjs_client.py",
    "services/azure_devops_service.py",

    # RAG
    "rag/__init__.py",
    "rag/chunker.py",
    "rag/context_builder.py",
    "rag/ingestion.py",
    "rag/retrieval.py",
    "rag/embeddings.py",

    # Documents
    "documents/__init__.py",
    "documents/extractor.py",
    "documents/processor.py",

    # Repositories
    "repositories/__init__.py",
    "repositories/knowledge_repository.py",

    # Schemas
    "schemas/__init__.py",
    "schemas/chat.py",
    "schemas/users.py",
    "schemas/work_items.py",
    "schemas/documents.py",
    "schemas/generation.py",

    # MCP
    "integrations/__init__.py",
    "integrations/mcp/__init__.py",
    "integrations/mcp/server.py",
    "integrations/mcp/azure_devops.py",
    "integrations/mcp/rag.py",

    # Guardrails
    "guardrails/__init__.py",
    "guardrails/input_validation.py",
    "guardrails/permission_checks.py",
    "guardrails/user_resolution.py",
    "guardrails/action_confirmation.py",
    "guardrails/output_validation.py",
]

created = 0
existing = 0

for relative_path in files:
    file_path = ROOT / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        existing += 1
        print(f"EXISTS: {relative_path}")
    else:
        file_path.touch()
        created += 1
        print(f"CREATED: {relative_path}")

# Tests: single folder, no subfolders
tests_dir = ROOT.parent / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)

print("\nStructure setup complete!")
print(f"Created: {created}")
print(f"Already existing: {existing}")
print(f"Tests folder: {tests_dir}")
