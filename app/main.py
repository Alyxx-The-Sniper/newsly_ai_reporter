from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile, shutil, os

from .config import settings
from .db import Base, engine
from .services.transcription import transcribe_fast
from .services.vision import describe_image
from .services.reporter import generate_report, latest_ai_report, revise_report
from .services.saver import save_report
from sqlalchemy import text

# add these imports near the top (after other imports)
from gradio import mount_gradio_app
from .gradio_ui import build_ui


app = FastAPI(title="News Reporter API", version="1.0")

# create tables on startup
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(engine)
    # add columns if missing
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS image_description TEXT"))
            conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS transcription_key VARCHAR"))
            conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS image_desc_key VARCHAR"))
        else:  # SQLite fallback (ignore if already exists)
            for ddl in [
                "ALTER TABLE reports ADD COLUMN image_description TEXT",
                "ALTER TABLE reports ADD COLUMN transcription_key VARCHAR",
                "ALTER TABLE reports ADD COLUMN image_desc_key VARCHAR",
            ]:
                try:
                    conn.execute(text(ddl))
                except Exception:
                    pass





@app.post("/generate")
async def generate(audio: UploadFile | None = File(default=None), image: UploadFile | None = File(default=None)):
    if not audio and not image:
        return JSONResponse({"message": "Upload an audio and/or image file."}, status_code=400)

    tmpdir = tempfile.mkdtemp()
    state = {"news_report": []}
    try:
        if audio:
            audio_path = os.path.join(tmpdir, audio.filename or "audio.wav")
            with open(audio_path, "wb") as f:
                shutil.copyfileobj(audio.file, f)
            state["audio_path"] = audio_path
            state = transcribe_fast(state)
        if image:
            image_path = os.path.join(tmpdir, image.filename or "image.jpg")
            with open(image_path, "wb") as f:
                shutil.copyfileobj(image.file, f)
            state["image_path"] = image_path
            state = describe_image(state)

        state = generate_report(state)
        return {
            "transcription": state.get("transcribed_text"),
            "report": latest_ai_report(state),
            "state": {k: v for k, v in state.items() if k in ("audio_path", "image_path", "transcribed_text", "image_description")},
        }
    finally:
        pass  # keep tmp files for optional save/upload; they live under tmpdir


@app.post("/revise")
async def revise_api(report: str = Form(...), feedback: str = Form(...), transcription: str | None = Form(default=None)):
    state = {
        "transcribed_text": transcription or "Not available.",
        "news_report": [
            # mimic prior AI message
            type("Msg", (), {"content": report})()
        ],
        "current_feedback": feedback,
    }
    state = revise_report(state)
    return {"revised_report": latest_ai_report(state)}


@app.post("/save")
async def save_api(report: str = Form(...), transcription: str | None = Form(default="")):
    state = {"news_report": [type("Msg", (), {"content": report})()], "transcribed_text": transcription}
    status = save_report(state)
    return {"status": str(status)}


from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse(url="/ui", status_code=307)



app = mount_gradio_app(app, build_ui(), path="/ui")  # UI at /ui