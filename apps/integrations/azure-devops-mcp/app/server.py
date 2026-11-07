from fastmcp import FastMCP

mcp = FastMCP("azure-devops-work-items")


@mcp.tool()
def server_status() -> dict[str, str]:
    """Return a safe status response while Azure DevOps tools are being configured."""
    return {"status": "scaffold-ready", "message": "Azure DevOps tools are not configured yet."}
