import uuid
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# Structured imports from our new modular architecture
from config import ARTIFACTS_DIR
from agents import agent_1, agent_2, agent_3

import state_manager

app = FastAPI(title="AISA v2 - Robust Foundation")

@app.on_event("startup")
def on_startup():
    print("--- AISA Server Starting Up ---")
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    print(f"Artifacts will be stored in: {ARTIFACTS_DIR}")
    
    print("Checking for ADB devices...")
    try:
        # Use shell=True for Windows compatibility
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, check=True, shell=True
        )
        print("ADB check successful:\n", result.stdout)
    except FileNotFoundError:
        print("ADB command not found. Please ensure it's in your system's PATH.")
    except Exception as e:
        print(f"ADB check failed: {e}")
        
    print("--- Startup complete. Waiting for tasks. ---")

@app.post("/create_task", status_code=201)
async def create_task(
    instructions: str = Form(...),
    platform: str = Form(..., enum=["mobile", "web"]),
    pdf: UploadFile = File(...)
):
    seq_no = uuid.uuid4().hex[:10]
    task_dir = state_manager.get_task_dir(seq_no)

    # Create the initial state file
    state_manager.create_task_state(seq_no, platform, instructions)
    
    pdf_path = task_dir / "input.pdf"
    with pdf_path.open("wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    state_manager.update_task_state(seq_no, {"status": "processing"})
    
    # --- Agent Pipeline ---
    blueprint = agent_1.run_agent1(seq_no, task_dir, pdf_path, instructions, platform)
    state_manager.update_task_state(seq_no, {"status": "blueprint_created"})

    artifacts = agent_2.run_agent2(seq_no, task_dir, blueprint)
    
    final_state = state_manager.update_task_state(seq_no, {
        "status": "ready",
        "artifacts": artifacts
    })
    
    print(f"Task {seq_no} created successfully and is ready for execution.")
    return final_state

@app.post("/run/{seq_no}")
async def run_task(seq_no: str):
    task_info = state_manager.get_task_state(seq_no)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task_info["status"] != "ready":
        raise HTTPException(status_code=400, detail=f"Task not ready. Status: {task_info['status']}")

    task_dir = state_manager.get_task_dir(seq_no)
    result = agent_3.run_agent3(seq_no, task_dir, task_info["platform"])

    return state_manager.update_task_state(seq_no, {"status": result["status"]})

@app.get("/task/{seq_no}")
async def get_task_status(seq_no: str):
    task_info = state_manager.get_task_state(seq_no)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    # Check for the result file from Agent 3 to see if a running task has finished
    result_file = state_manager.get_task_dir(seq_no) / "agent3" / "result.txt"
    if result_file.exists() and task_info["status"] == "running":
        new_status = result_file.read_text().strip()
        return state_manager.update_task_state(seq_no, {"status": new_status})
        
    return task_info