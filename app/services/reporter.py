from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ..config import settings

llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=settings.openai_api_key)


def generate_report(state: Dict) -> Dict:
    ctx = ["You are an expert news reporter. Write a clear, concise, factual report based on the inputs."]
    t = state.get("transcribed_text")
    d = state.get("image_description")
    if not t and not d:
        content = "No input provided. Upload an audio file and/or image."
    else:
        if t:
            ctx.append(f"--- Transcribed Audio ---\"{t}\"")
        if d:
            ctx.append(f"--- Image Description ---\"{d}\"")
        ctx.append("Present the information as a professional news report. If both are present, synthesize them.")
        content = llm.invoke([SystemMessage(content="".join(ctx))]).content
    state.setdefault("news_report", [])
    state["news_report"].append(AIMessage(content=content))
    return state


def revise_report(state: Dict) -> Dict:
    t = state.get("transcribed_text", "Not available.")
    last = next((m for m in reversed(state.get("news_report", [])) if isinstance(m, AIMessage)), None)
    draft = last.content if last else "No report yet."
    fb = state.get("current_feedback", "No feedback provided.")
    prompt = f"""
You are a professional news editor. Revise the report per feedback. Keep facts faithful to the transcription.

**Original Transcription:**
"{t}"

**Current Draft:**
"{draft}"

**Feedback:**
"{fb}"

Return only the full revised report.
"""
    revised = llm.invoke([HumanMessage(content=prompt)])
    state.setdefault("news_report", [])
    state["news_report"].append(revised)
    return state


def latest_ai_report(state: Dict) -> str:
    msgs = [m for m in state.get("news_report", []) if isinstance(m, AIMessage)]
    return msgs[-1].content if msgs else "No report generated yet."