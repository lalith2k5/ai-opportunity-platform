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
