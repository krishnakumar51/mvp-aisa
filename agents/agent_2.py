from pathlib import Path
import json
from fastapi import HTTPException

from llm_utils import get_llm_response, extract_code_from_response

# --- Agent 2's Internal Knowledge Base ---

MOBILE_SETUP_TEMPLATE = """
import time
import random
import subprocess
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

def setup_driver(app_package, app_activity):
    \"\"\"Initializes and returns a robust Appium driver.\"\"\"
    try:
        print("Setting up Appium driver...")
        options = UiAutomator2Options()
        options.platform_name = 'Android'
        options.automation_name = 'UiAutomator2'
        options.app_package = app_package
        options.app_activity = app_activity
        options.no_reset = False
        options.full_reset = False
        options.new_command_timeout = 300
        options.auto_grant_permissions = True
        
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        print("✓ Driver is ready.")
        return driver
    except Exception as e:
        print(f"✗ Driver setup failed: {e}")
        return None
"""

WEB_SETUP_TEMPLATE = """
from playwright.sync_api import sync_playwright, Playwright, expect
import time

def run(playwright: Playwright) -> None:
    \"\"\"Main function to run the web automation script.\"\"\"
    print("Setting up browser...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()
    page.set_default_timeout(60000)
    print("✓ Browser is ready.")
"""

# --- Agent 2's Core Logic ---

def run_agent2(seq_no: str, blueprint: dict) -> dict:
    """
    Agent 2: Generates a runnable automation script using its internal,
    production-grade setup templates and the provided blueprint.
    """
    print(f"[{seq_no}] Running Agent 2: Agentic Code Generation")
    out_dir = Path("generated_code") / seq_no / "agent2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    platform = blueprint.get("platform", "web")
    
    # 1. Select the appropriate internal knowledge template
    if platform == "mobile":
        setup_code = MOBILE_SETUP_TEMPLATE
        framework = "Appium"
        dependency = "Appium-Python-Client==3.6.0\nselenium==4.22.0" 
    else:
        setup_code = WEB_SETUP_TEMPLATE
        framework = "Playwright"
        dependency = "playwright==1.45.0"

    # 2. Define prompts and call LLM for code generation
    system_prompt = (
        f"You are an expert Python automation developer specializing in {framework}. Your task is to write a complete, "
        f"runnable Python script based on the provided JSON blueprint. \n"
        f"**CRITICAL INSTRUCTION:** You MUST use the provided setup code for driver/browser initialization. It is proven and reliable. "
        f"After the setup, implement the logic for the steps from the blueprint. Generate random, realistic data for inputs like emails, passwords, and names. "
        f"Import all necessary libraries. The final script should be self-contained and executable in a main block. "
        f"Respond with ONLY the Python code inside a markdown block."
    )
    user_prompt = f"""
    **JSON Blueprint:**
    ---
    {json.dumps(blueprint, indent=2)}
    ---
    **MANDATORY Setup Code (Use this to start your script):**
    ---
    ```python
    {setup_code}
    ```
    ---
    Generate the complete, runnable Python {framework} script now.
    """
    
    try:
        response_text = get_llm_response(user_prompt, system_prompt)
        script_code = extract_code_from_response(response_text)
        
        script_path = out_dir / "automation_script.py"
        reqs_path = out_dir / "requirements.txt"
        
        script_path.write_text(script_code, encoding="utf-8")
        reqs_path.write_text(dependency, encoding="utf-8")

        print(f"[{seq_no}] Agent 2 finished successfully. Script generated at {script_path}")
        return {"script": str(script_path), "requirements": str(reqs_path)}
    except Exception as e:
        print(f"[{seq_no}] Agent 2 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 2 (Code Gen) failed: {e}")
