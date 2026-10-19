from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class ChatQuery(BaseModel):
    question: str
    session_id: Optional[int] = None
    context_kind: Optional[str] = None
    context_id: Optional[str] = None
    context_title: Optional[str] = None
    context_summary: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    source: Optional[str] = None
    mode: Optional[str] = "quick"  # "quick" or "deep"

class OpportunityResponse(BaseModel):
    id: int
    title: str
    description: str
    opportunity_score: float
    confidence_score: float
    demand_score: float
    research_gap_score: float
    trend_score: float
    innovation_score: float = 0.0
    competition_score: float = 0.0
    feasibility_score: float = 0.0
    market_readiness_score: float = 0.0
    explanation: Optional[str] = None
    class Config:
        from_attributes = True
    status: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    problem_type: Optional[str] = None
    opportunity_score_spec: Optional[float] = None
    confidence_spec: Optional[int] = None
    weights_version: Optional[str] = None
    confidence_version: Optional[str] = None
    trend_window: Optional[int] = None
    evidence_sources: Optional[list] = None
    related_technologies: Optional[list] = None
    existing_research: Optional[list] = None
    suggested_research_direction: Optional[str] = None
    suggested_project_direction: Optional[str] = None
    known_limitations: Optional[str] = None
class ProblemClusterResponse(BaseModel):
    id: int
    title: str
    description: str
    keywords: Optional[List[str]] = []
    source_count: int
    demand_score: float
    class Config:
        from_attributes = True

class ResearchGapResponse(BaseModel):
    id: int
    title: str
    description: str
    gap_score: float
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    class Config:
        from_attributes = True


class SearchHistoryResponse(BaseModel):
    id: int
    query: str
    results_count: int
    created_at: Any
    class Config:
        from_attributes = True


class ProblemProfileResponse(BaseModel):
    id: int
    organization: Optional[str] = ""
    problem_title: str
    problem_description: Optional[str] = ""
    industry_domain: Optional[str] = "Other"
    problem_type: Optional[str] = "Other"
    technology_stage: Optional[str] = "potential"
    required_technology: Optional[List[str]] = []
    current_approach: Optional[str] = ""
    known_limitations: Optional[str] = ""
    expected_outcome: Optional[str] = ""
    source: Optional[str] = ""
    source_url: Optional[str] = ""
    keywords: Optional[List[str]] = []
    problem_status: Optional[str] = "unknown"
    student_suitability: Optional[str] = "medium"
    extracted_by: Optional[str] = ""
    created_at: Any
    class Config:
        from_attributes = True
