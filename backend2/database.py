from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class RequestRecord(Base):
    __tablename__ = "requests"

    request_id = Column(String, primary_key=True)
    college = Column(String)
    document_type = Column(String)
    urgency = Column(Integer)
    requester_type = Column(String)

    submission_time = Column(DateTime)
    assignment_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)

    status = Column(String)
    priority_score = Column(Float)

engine = create_engine("sqlite:///simulation.db")
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)