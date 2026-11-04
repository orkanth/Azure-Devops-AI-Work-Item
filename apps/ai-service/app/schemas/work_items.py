
from pydantic import BaseModel, Field


class TaskProposal(BaseModel):
    title: str = Field(min_length=3)
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class UserStoryProposal(BaseModel):
    title: str = Field(min_length=3)
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    tasks: list[TaskProposal] = Field(default_factory=list)


class FeatureProposal(BaseModel):
    title: str = Field(min_length=3)
    description: str
    user_stories: list[UserStoryProposal] = Field(
        default_factory=list
    )


class EpicProposal(BaseModel):
    title: str = Field(min_length=3)
    description: str
    features: list[FeatureProposal] = Field(
        default_factory=list
    )


class GenerateWorkItemsRequest(BaseModel):
    requirement: str = Field(
        min_length=10,
        description="Business requirement for work-item generation",
    )


class GenerateWorkItemsResponse(BaseModel):
    status: str
    message: str
    requirement: str
    epic: EpicProposal | None = None
