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

class OpportunityResponse(BaseModel):
    id: int
    title: str
    description: str
    opportunity_score: float
    confidence_score: float
    demand_score: float
    research_gap_score: float
    trend_score: float
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
