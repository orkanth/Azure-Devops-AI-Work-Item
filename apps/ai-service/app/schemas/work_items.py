from pydantic import BaseModel, Field
from typing import Literal
from pydantic import BaseModel, Field, model_validator

WorkItemType = Literal[
    "Epic",
    "Feature",
    "User Story",
    "Task",
    "Bug",
]


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
    user_stories: list[UserStoryProposal] = Field(default_factory=list)


class EpicProposal(BaseModel):
    title: str = Field(min_length=3)
    description: str
    features: list[FeatureProposal] = Field(default_factory=list)


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


class WorkItemProposal(BaseModel):
    """Platform-independent work-item proposal."""

    type: WorkItemType
    title: str = Field(min_length=3, max_length=255)
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)

    children: list["WorkItemProposal"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_child_types(self):
        allowed_children = {
            "Epic": {"Feature", "User Story", "Task", "Bug"},
            "Feature": {"User Story", "Task", "Bug"},
            "User Story": {"Task", "Bug"},
            "Task": set(),
            "Bug": set(),
        }

        for child in self.children:
            if child.type not in allowed_children[self.type]:
                raise ValueError(f"{child.type} cannot be created under {self.type}.")

        return self


class WorkItemGenerationProposal(BaseModel):
    """Complete generation result for any supported work-item type."""

    requested_type: WorkItemType

    items: list[WorkItemProposal] = Field(min_length=1)

    parent_reference: str | None = None


class GenerationIntent(BaseModel):
    """Extract the user's work-item generation intent."""

    requested_type: WorkItemType

    requirement: str = Field(
        min_length=10,
        description="The actual business or technical requirement.",
    )
