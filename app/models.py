import datetime as _dt
from sqlalchemy import Column, String, DateTime, Text
from .db import Base

class ReportRecord(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=_dt.datetime.utcnow)
    audio_key = Column(String)
    report_key = Column(String)
    transcription = Column(Text)
    final_report = Column(Text)
    # NEW
    image_description = Column(Text)
    transcription_key = Column(String)
    image_desc_key = Column(String)


