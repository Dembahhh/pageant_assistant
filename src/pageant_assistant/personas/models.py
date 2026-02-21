"""Pydantic models for contestant personas."""

import uuid
from pydantic import BaseModel, Field


class PersonalStory(BaseModel):
    """A single personal story/experience the contestant can draw from."""

    title: str = Field(
        ..., min_length=1, max_length=120,
        description="Short label, e.g. 'Teaching in Rural Zambia'",
    )
    text: str = Field(
        ..., min_length=10,
        description="The story in 2-4 sentences",
    )
    key_lesson: str = Field(
        ..., min_length=5,
        description="One-sentence takeaway the contestant learned",
    )


class Persona(BaseModel):
    """Full contestant persona profile."""

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12],
        description="Unique persona identifier",
    )
    name: str = Field(
        ..., min_length=1, max_length=100,
        description="Contestant's name",
    )
    country: str = Field(
        ..., min_length=1, max_length=100,
        description="Country of representation",
    )
    platform: str = Field(
        ..., min_length=1,
        description="Advocacy platform, e.g. 'Mental health for youth'",
    )
    values: list[str] = Field(
        default_factory=list,
        description="Core values, e.g. ['resilience', 'empathy', 'education']",
    )
    personal_stories: list[PersonalStory] = Field(
        default_factory=list,
        description="Personal experiences to draw from in answers",
    )
