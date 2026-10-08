from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator
from sqlalchemy import DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from patentllm.config import get_settings
from patentllm.schemas import PatentRecord, PatentReport

class Base(DeclarativeBase):
    pass

class PatentDocument(Base):
    __tablename__ = "patent_documents"
    patent_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(Text, default="")
    abstract: Mapped[str] = mapped_column(Text, default="")
    claims: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ReportRun(Base):
    __tablename__ = "report_runs"
    report_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(128))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def get_engine(db_url: str | None = None):
    return create_engine(db_url or get_settings().db_url, future=True)

def init_db(db_url: str | None = None) -> None:
    Base.metadata.create_all(get_engine(db_url))

@contextmanager
def session_scope(db_url: str | None = None) -> Iterator[Session]:
    engine = get_engine(db_url)
    session = sessionmaker(bind=engine, expire_on_commit=False, future=True)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def upsert_patents(records: list[PatentRecord], db_url: str | None = None) -> int:
    init_db(db_url)
    with session_scope(db_url) as session:
        for record in records:
            payload = record.model_dump_json()
            doc = session.get(PatentDocument, record.patent_id)
            if doc is None:
                session.add(PatentDocument(
                    patent_id=record.patent_id, title=record.title, abstract=record.abstract,
                    claims=record.claims, description=record.description, payload_json=payload
                ))
            else:
                doc.title, doc.abstract, doc.claims, doc.description, doc.payload_json = (
                    record.title, record.abstract, record.claims, record.description, payload
                )
    return len(records)

def load_patents(db_url: str | None = None) -> list[PatentRecord]:
    init_db(db_url)
    with session_scope(db_url) as session:
        docs = session.execute(select(PatentDocument)).scalars().all()
        return [PatentRecord.model_validate_json(doc.payload_json) for doc in docs]

def save_report(report: PatentReport, db_url: str | None = None) -> None:
    init_db(db_url)
    with session_scope(db_url) as session:
        session.merge(ReportRun(
            report_id=report.report_id, query=report.query, audience=report.audience.value,
            model=report.model, payload_json=report.model_dump_json()
        ))

def get_report(report_id: str, db_url: str | None = None) -> PatentReport | None:
    init_db(db_url)
    with session_scope(db_url) as session:
        row = session.get(ReportRun, report_id)
        return PatentReport.model_validate_json(row.payload_json) if row else None
