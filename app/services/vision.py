import base64
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..config import settings

vision_llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=settings.openai_api_key)


def describe_image(state: Dict) -> Dict:
    image_path: Optional[str] = state.get("image_path")
    if not image_path:
        state["image_description"] = None
        return state
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        msg = HumanMessage(content=[
            {"type": "text", "text": "Describe the image in detail"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ])
        state["image_description"] = vision_llm.invoke([msg]).content
    except FileNotFoundError:
        state["image_description"] = "Error: Image file not found."
    except Exception as e:
        state["image_description"] = f"Error during image description: {e}"
    return state