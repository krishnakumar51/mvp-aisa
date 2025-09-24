from pathlib import Path
import json
import fitz  # PyMuPDF
from fastapi import HTTPException

from llm_utils import get_llm_response, extract_json_from_response

def run_agent1(seq_no: str, task_dir: Path, pdf_path: Path, instructions: str, platform: str) -> dict:
    """
    Agent 1: Parses a PDF for text and images, then uses an LLM to generate
    a detailed JSON blueprint for the automation task.
    """
    print(f"[{seq_no}] Running Agent 1: Blueprint Generation")
    out_dir = task_dir / "agent1"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract text and images from the PDF
    pdf_text_content, image_paths = "", []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            pdf_text_content += f"\n--- PDF Page {page_num + 1} Text ---\n{page.get_text()}"
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes, image_ext = base_image["image"], base_image["ext"]
                image_filename = f"page{page_num+1}_img{img_index}.{image_ext}"
                image_filepath = out_dir / image_filename
                image_filepath.write_bytes(image_bytes)
                image_paths.append(str(image_filepath))
        print(f"[{seq_no}] Extracted {len(image_paths)} images and text from PDF.")
    except Exception as e:
        print(f"[{seq_no}] Warning: PDF processing failed: {e}")
        pdf_text_content = "Could not read PDF. Relying on user instructions only."

    # 2. Define prompts and call LLM for the blueprint
    system_prompt = (
        "You are a master test automation planner. Your task is to create a detailed JSON blueprint for an automation script. "
        "The JSON output MUST be a single object with two top-level keys: 'summary' and 'steps'.\n"
        "1. The 'summary' object must contain: 'goal' (a concise summary of the overall objective from user instructions), "
        "'target_application' (the application name or package ID, inferred from the context, e.g., 'com.microsoft.office.outlook' or 'Outlook Web'), and 'platform'.\n"
        "2. The 'steps' array must contain a list of sequential actions. Each step must include: 'step_id', 'screen_name', "
        "'description', 'action' (e.g., 'click', 'type_text'), 'target_element_description', "
        "'value_to_enter' (or null), and 'associated_image' (or null).\n"
        "Respond with ONLY the JSON content."
    )
    user_prompt = f"""
    Platform: {platform}
    User Instructions: --- {instructions} ---
    Extracted PDF Text: --- {pdf_text_content} ---
    Available Image Files for Context: --- {', '.join([Path(p).name for p in image_paths])} ---
    Generate the detailed JSON blueprint.
    """
    
    try:
        response_text = get_llm_response(user_prompt, system_prompt)
        blueprint = extract_json_from_response(response_text)
        
        # Save the blueprint to a file
        blueprint_path = out_dir / "blueprint.json"
        blueprint_path.write_text(json.dumps(blueprint, indent=2), encoding="utf-8")
        
        print(f"[{seq_no}] Agent 1 finished successfully. Blueprint created at {blueprint_path}")
        return blueprint
    except (ValueError, Exception) as e:
        print(f"[{seq_no}] Agent 1 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 1 (Blueprint) failed: {e}")
