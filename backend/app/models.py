from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RawDocument(Base):
    __tablename__ = "raw_documents"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    external_id = Column(String, index=True)
    title = Column(Text)
    content = Column(Text)
    url = Column(Text)
    author = Column(String)
    metadata_json = Column(JSON)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)

class ProcessedDocument(Base):
    __tablename__ = "processed_documents"
    id = Column(Integer, primary_key=True, index=True)
    raw_document_id = Column(Integer, ForeignKey("raw_documents.id"))
    cleaned_text = Column(Text)
    keywords = Column(JSON)
    entities = Column(JSON)
    topics = Column(JSON)
    sentiment_score = Column(Float)
    embedding_id = Column(String)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

class ProblemCluster(Base):
    __tablename__ = "problem_clusters"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    keywords = Column(JSON)
    source_count = Column(Integer, default=0)
    demand_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ResearchGap(Base):
    __tablename__ = "research_gaps"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    problem_cluster_id = Column(Integer, ForeignKey("problem_clusters.id"))
    gap_score = Column(Float, default=0.0)
    evidence = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Trend(Base):
    __tablename__ = "trends"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    trend_score = Column(Float, default=0.0)
    source_data = Column(JSON)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    problem_cluster_id = Column(Integer, ForeignKey("problem_clusters.id"))
    research_gap_id = Column(Integer, ForeignKey("research_gaps.id"))
    demand_score = Column(Float, default=0.0)
    research_gap_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    innovation_score = Column(Float, default=0.0)
    competition_score = Column(Float, default=0.0)
    feasibility_score = Column(Float, default=0.0)
    market_readiness_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    evidence = Column(JSON)
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(Text)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    sources = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True)
    action = Column(String)
    status = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    report_type = Column(String)
    content = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String, index=True)  # research_opportunity, emerging_tech, startup_opportunity, innovation_alert, research_gap_alert
    title = Column(String, nullable=False)
    message = Column(Text)
    link = Column(String)
    severity = Column(String, default="info")  # info, warning, success
    read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeGraphNode(Base):
    __tablename__ = "kg_nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    entity_type = Column(String, index=True)
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeGraphEdge(Base):
    __tablename__ = "kg_edges"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True, nullable=False)
    target = Column(String, index=True, nullable=False)
    relation = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    trend_name = Column(String, index=True, nullable=False)
    mention_count = Column(Integer, default=0)
    source_count = Column(Integer, default=0)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
