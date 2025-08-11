# app/services/saver.py
import os
import uuid
import datetime as _dt
from typing import Dict

from ..storage import upload_to_s3 #presign_url  # presign_url must exist in storage.py
from ..db import SessionLocal, Base, engine
from ..models import ReportRecord
from ..config import settings

# Ensure tables exist (idempotent)
Base.metadata.create_all(engine)


class SaveResult(str):
    """Lightweight typed string for status messages."""
    pass


def save_report(state: Dict) -> SaveResult:
    # Require a generated report
    if not state.get("news_report"):
        return SaveResult("No report available to save.")

    # Extract report + optional fields
    last = state["news_report"][-1]
    final_text = getattr(last, "content", str(last))
    transcribed_text = state.get("transcribed_text", "")
    image_desc = state.get("image_description", "")

    # 1) Write local files
    out_dir = "saved_reports"
    os.makedirs(out_dir, exist_ok=True)

    report_path = os.path.join(out_dir, "news_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    trans_path = None
    if transcribed_text:
        trans_path = os.path.join(out_dir, "transcription.txt")
        with open(trans_path, "w", encoding="utf-8") as f:
            f.write(transcribed_text)

    imgdesc_path = None
    if image_desc:
        imgdesc_path = os.path.join(out_dir, "image_description.txt")
        with open(imgdesc_path, "w", encoding="utf-8") as f:
            f.write(image_desc)

    # 2) Keys (no audio upload by design)
    uid = uuid.uuid4().hex
    ts = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_key = f"{settings.s3_prefix}report_{ts}_{uid}.txt"
    trans_key = f"{settings.s3_prefix}transcription_{ts}_{uid}.txt" if trans_path else ""
    imgdesc_key = f"{settings.s3_prefix}image_description_{ts}_{uid}.txt" if imgdesc_path else ""

    # 3) Upload + presign (objects are private; no ACLs)
    report_uri = upload_to_s3(report_path, report_key)
    # report_dl = presign_url(report_key, expires=3600)

    trans_uri = trans_dl = ""
    if trans_path:
        trans_uri = upload_to_s3(trans_path, trans_key)
        # trans_dl = presign_url(trans_key, expires=3600)

    imgdesc_uri = imgdesc_dl = ""
    if imgdesc_path:
        imgdesc_uri = upload_to_s3(imgdesc_path, imgdesc_key)
        # imgdesc_dl = presign_url(imgdesc_key, expires=3600)

    # 4) Persist to DB (no audio fields)
    with SessionLocal() as db:
        rec = ReportRecord(
            id=uid,
            audio_key="",  # audio not saved by design
            report_key=str(report_uri),
            transcription=transcribed_text,
            final_report=final_text,
            # new columns if you added them:
            image_description=image_desc if hasattr(ReportRecord, "image_description") else None,
            transcription_key=str(trans_uri) if trans_uri and hasattr(ReportRecord, "transcription_key") else None,
            image_desc_key=str(imgdesc_uri) if imgdesc_uri and hasattr(ReportRecord, "image_desc_key") else None,
        )
        db.add(rec)
        db.commit()

    # 5) Status message
    lines = [
        f"✅ Saved local text: {report_path}",
        f"   Report (S3): {report_uri}",

    ]
    if trans_path:
        lines += [f"   Transcription (S3): {trans_uri}", f"   Download (1h): {trans_dl}"]
    if imgdesc_path:
        lines += [f"   Image description (S3): {imgdesc_uri}", f"   Download (1h): {imgdesc_dl}"]
    lines += ["   (Audio not saved by design)"]
    return SaveResult("\n".join(lines))
