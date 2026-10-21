from fastapi import FastAPI

app = FastAPI(
    title="Azure DevOps AI Work Item Generator",
    version="0.1.0",
    description="AI service scaffold for prompt and document-driven work item generation.",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-service"}
