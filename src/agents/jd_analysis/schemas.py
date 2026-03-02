from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SeniorityLevel(BaseModel):
    value: Literal["junior", "mid", "senior", "lead", "principal", "ambiguous", "unknown"]
    ambiguous: bool
    evidence: List[str] = Field(default_factory=list)


class Signals(BaseModel):
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    seniority_level: SeniorityLevel
    tools_tech_stack: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    location_region: Optional[str] = None
    language_requirements: List[str] = Field(default_factory=list)
    visa_or_regulatory_constraints: List[str] = Field(default_factory=list)


class ImplicitSignal(BaseModel):
    signal: str
    inferred: Literal[True]
    evidence: List[str] = Field(default_factory=list)


class HardSoftLabels(BaseModel):
    hard_requirements: List[str] = Field(default_factory=list)
    soft_preferences: List[str] = Field(default_factory=list)


class JDAnalysisOutput(BaseModel):
    agent_name: Literal["jd_analysis"]
    signals: Signals
    implicit_signals: List[ImplicitSignal] = Field(default_factory=list)
    hard_vs_soft_labels: HardSoftLabels
    warnings: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
