import uuid
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# Structured imports from our new modular architecture
from config import ARTIFACTS_DIR
from agents import agent_1, agent_2, agent_3

# In-memory DB for task state (to be replaced in Phase 2)
TASKS = {}

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
    task_dir = ARTIFACTS_DIR / seq_no
    task_dir.mkdir(exist_ok=True)
    
    pdf_path = task_dir / "input.pdf"
    with pdf_path.open("wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    TASKS[seq_no] = {"status": "processing", "platform": platform}
    
    # --- Agent Pipeline ---
    blueprint = agent_1.run_agent1(seq_no, pdf_path, instructions, platform)
    artifacts = agent_2.run_agent2(seq_no, blueprint)
    
    TASKS[seq_no].update({
        "status": "ready",
        "artifacts": artifacts
    })
    
    print(f"Task {seq_no} created successfully and is ready for execution.")
    return TASKS[seq_no]

@app.post("/run/{seq_no}")
async def run_task(seq_no: str):
    task_info = TASKS.get(seq_no)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task_info["status"] != "ready":
        raise HTTPException(status_code=400, detail=f"Task not ready. Status: {task_info['status']}")

    result = agent_3.run_agent3(seq_no, task_info["platform"])
    task_info["status"] = result["status"]
    return task_info

@app.get("/task/{seq_no}")
async def get_task_status(seq_no: str):
    task_info = TASKS.get(seq_no)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    result_file = ARTIFACTS_DIR / seq_no / "agent3" / "result.txt"
    if result_file.exists() and task_info["status"] == "running":
        task_info["status"] = result_file.read_text().strip()
        
    return task_info