
from pydantic import BaseModel, Field


class DocumentQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask about uploaded documents.",
    )

    project_id: str = Field(
        ...,
        min_length=1,
        description="Project containing the uploaded documents.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of relevant chunks to retrieve.",
    )
