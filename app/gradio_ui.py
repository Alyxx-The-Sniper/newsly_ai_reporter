import gradio as gr
from typing import Optional, Dict

from .services.transcription import transcribe_fast
from .services.vision import describe_image
from .services.reporter import generate_report, latest_ai_report, revise_report
from .services.saver import save_report


def generate_report_ui(audio_filepath: Optional[str], image_filepath: Optional[str]):
    if not audio_filepath and not image_filepath:
        return None, "", "", "", gr.update(visible=False), "Upload a file to begin."

    state: Dict = {
        "audio_path": audio_filepath,
        "image_path": image_filepath,
        "news_report": [],
    }

    if state.get("audio_path"):
        state = transcribe_fast(state)
    if state.get("image_path"):
        state = describe_image(state)

    state = generate_report(state)

    report_text = latest_ai_report(state)
    transcribed_text = state.get("transcribed_text", "")
    image_desc = state.get("image_description", "")

    return state, report_text, transcribed_text, image_desc, gr.update(visible=True), "Initial report generated. Ready for feedback."


def revise_report_ui(feedback: str, current_state: Dict):
    if not current_state:
        return current_state, "", "No report yet. Generate first."
    if not feedback.strip():
        return current_state, latest_ai_report(current_state), "⚠️ Please provide feedback to revise the report."

    current_state["current_feedback"] = feedback
    revised_state = revise_report(current_state)
    report_text = latest_ai_report(revised_state)
    return revised_state, report_text, "✅ Report revised. You can provide more feedback or save."


def save_report_ui(current_state: Dict):
    if not current_state:
        return "No report available to save."
    return save_report(current_state)


def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), title="News Reporter (Gradio)") as demo:
        agent_state = gr.State(value=None)

        gr.Markdown("# 🤖 News Reporter (Gradio)")
        gr.Markdown("Upload an audio recording and/or an image to generate a news report. Then revise and save.")

        with gr.Row():
            audio_input = gr.Audio(type="filepath", label="Audio")
            image_input = gr.Image(type="filepath", label="Image")

        generate_btn = gr.Button("Generate", variant="primary", scale=1)
        gr.Markdown("---")
        with gr.Row():
            transcription_display = gr.Textbox(label="📝 Transcription", interactive=False, lines=12, show_copy_button=True)
            report_display = gr.Textbox(label="📰 Report", interactive=False, lines=12, show_copy_button=True)
        with gr.Row():
            image_desc_display = gr.Textbox(label="🖼️ Image Description", interactive=False, lines=8, show_copy_button=True)

        with gr.Group(visible=False) as revision_group:
            gr.Markdown("### ✍️ Provide Feedback to Revise Report")
            feedback_input = gr.Textbox(label="Your Feedback", placeholder="e.g., 'Make the tone more urgent.' or 'Clarify the second paragraph.'")
            with gr.Row():
                revise_btn = gr.Button("Revise")
                save_btn = gr.Button("Save & Finish", variant="stop")

        status_display = gr.Textbox(label="Status", interactive=False)

        generate_btn.click(
            fn=generate_report_ui,
            inputs=[audio_input, image_input],
            outputs=[agent_state, report_display, transcription_display, image_desc_display, revision_group, status_display],
        )

        revise_btn.click(
            fn=revise_report_ui,
            inputs=[feedback_input, agent_state],
            outputs=[agent_state, report_display, status_display],
        )

        save_btn.click(
            fn=save_report_ui,
            inputs=[agent_state],
            outputs=[status_display],
        )

    return demo