import re
import sys
from pathlib import Path

import gradio as gr

# Ensure project root is importable even when launched outside repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import rewrite_ka_institutional as core


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def run_rewrite(input_text: str, debug_mode: bool, batch_paragraphs: bool) -> str:
    text = (input_text or "").strip()
    if not text:
        return ""

    # Reuse existing backend logic unchanged; only toggle debug visibility.
    previous_debug = core.DEBUG
    core.DEBUG = debug_mode
    try:
        if batch_paragraphs:
            parts = _split_paragraphs(text)
            rewritten = [core._rewrite_text(part) for part in parts]
            return "\n\n".join(rewritten)

        return core._rewrite_text(text)
    finally:
        core.DEBUG = previous_debug


with gr.Blocks(title="Georgian Institutional Rewriter") as demo:
    gr.Markdown("## Georgian Institutional Rewriter")
    gr.Markdown("Paste one text or multiple paragraphs. Rewrites into cleaner institutional Georgian.")

    input_box = gr.Textbox(
        label="Input text",
        lines=12,
        placeholder="შეიყვანეთ ან ჩასვით ტექსტი...",
    )
    debug_toggle = gr.Checkbox(label="Debug mode", value=False)
    batch_toggle = gr.Checkbox(
        label="Process as multiple paragraphs (split by blank lines)",
        value=False,
    )

    rewrite_button = gr.Button("Rewrite")
    output_box = gr.Textbox(
        label="Rewritten text",
        lines=12,
    )

    rewrite_button.click(
        fn=run_rewrite,
        inputs=[input_box, debug_toggle, batch_toggle],
        outputs=output_box,
    )


if __name__ == "__main__":
    demo.launch()
