from pathlib import Path
import sys
import os
import subprocess
from fastapi import HTTPException

def run_agent3(seq_no: str, task_dir: Path, platform: str) -> dict:
    """
    Agent 3: Creates an isolated venv and executes the generated script.
    - For mobile, it starts the Appium server and the script in separate terminals.
    - For web, it ensures Playwright is installed and runs the script.
    """
    print(f"[{seq_no}] Running Agent 3 for '{platform}' platform.")
    agent2_dir = task_dir / "agent2"
    agent3_dir = task_dir / "agent3"
    agent3_dir.mkdir(parents=True, exist_ok=True)

    script_path = agent2_dir / "automation_script.py"
    reqs_path = agent2_dir / "requirements.txt"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Automation script not found for task {seq_no}.")

    venv_dir = agent3_dir / "env"
    python_executable = sys.executable

    # --- Platform-specific execution logic ---
    if platform == "mobile":
        # --- Mobile Flow: Two terminals (Appium Server + Script Executor) ---
        if sys.platform == "win32":
            # Script 1: Start Appium Server
            appium_script_commands = f"""
            @echo off
            title Appium Server ({seq_no})
            echo ---------------------------------
            echo   Starting Appium Server...
            echo   Task ID: {seq_no}
            echo   This window must remain open.
            echo ---------------------------------
            appium
            """
            appium_script_path = agent3_dir / "start_appium.bat"
            appium_script_path.write_text(appium_script_commands, encoding="utf-8")
            subprocess.Popen(f'start "Appium Server ({seq_no})" cmd /c "{appium_script_path}"', shell=True)

            # Script 2: Run Automation
            activate_script = venv_dir / "Scripts" / "activate.bat"
            run_script_commands = f"""
            @echo off
            title Automation Runner ({seq_no})
            echo --------------------------------------------------
            echo   AISA Mobile Automation Task: {seq_no}
            echo --------------------------------------------------
            cd /d "{agent3_dir}"
            echo [1/4] Creating virtual environment...
            "{python_executable}" -m venv env
            echo [2/4] Activating & installing dependencies...
            call "{activate_script}" & pip install --upgrade pip > nul & pip install -r "{reqs_path}"
            if %errorlevel% neq 0 (
                echo.
                echo ########## DEPENDENCY INSTALLATION FAILED ##########
                pause
                exit /b %errorlevel%
            )
            echo.
            echo Waiting 10s for Appium server to start...
            timeout /t 10 /nobreak > nul
            echo [3/4] Running automation script...
            echo --------------------------------------------------
            python "{script_path}"
            if %errorlevel% equ 0 (echo succeeded > result.txt) else (echo failed > result.txt)
            echo --------------------------------------------------
            echo [4/4] Script finished. This window can be closed.
            pause
            """
            run_script_path = agent3_dir / "run_automation.bat"
            run_script_path.write_text(run_script_commands, encoding="utf-8")
            subprocess.Popen(f'start "Automation Runner ({seq_no})" cmd /k "{run_script_path}"', shell=True)

        else:  # macOS / Linux
            # Script 1: Start Appium Server
            appium_script_commands = f"""#!/bin/bash
            echo "---------------------------------"
            echo "  Starting Appium Server..."
            echo "  Task ID: {seq_no}"
            echo "  This terminal must remain open."
            echo "---------------------------------"
            appium
            """
            appium_script_path = agent3_dir / "start_appium.sh"
            appium_script_path.write_text(appium_script_commands, encoding="utf-8")
            os.chmod(appium_script_path, 0o755)
            subprocess.Popen(['gnome-terminal', '--title', f'Appium Server ({seq_no})', '--', str(appium_script_path)])

            # Script 2: Run Automation
            activate_script = venv_dir / "bin" / "activate"
            run_script_commands = f"""#!/bin/bash
            echo "--------------------------------------------------"
            echo "  AISA Mobile Automation Task: {seq_no}"
            echo "--------------------------------------------------"
            cd "{agent3_dir}"
            echo "[1/4] Creating virtual environment..."
            "{python_executable}" -m venv env
            echo "[2/4] Activating & installing dependencies..."
            source "{activate_script}" && pip install --upgrade pip > /dev/null && pip install -r "{reqs_path}"
            if [ $? -ne 0 ]; then
                echo ""
                echo "########## DEPENDENCY INSTALLATION FAILED ##########"
                read -p "Press Enter to close..."
                exit 1
            fi
            echo ""
            echo "Waiting 10s for Appium server to start..."
            sleep 10
            echo "[3/4] Running automation script..."
            echo "--------------------------------------------------"
            python "{script_path}"
            if [ $? -eq 0 ]; then echo "succeeded" > result.txt; else echo "failed" > result.txt; fi
            echo "--------------------------------------------------"
            echo "[4/4] Script finished. Press Enter to close."
            read
            """
            run_script_path = agent3_dir / "run_automation.sh"
            run_script_path.write_text(run_script_commands, encoding="utf-8")
            os.chmod(run_script_path, 0o755)
            subprocess.Popen(['gnome-terminal', '--title', f'Automation Runner ({seq_no})', '--', str(run_script_path)])

    else:  # platform == "web"
        # --- Web Flow: Single terminal ---
        if sys.platform == "win32":
            activate_script = venv_dir / "Scripts" / "activate.bat"
            commands = f"""
            @echo off
            title Web Automation ({seq_no})
            echo --------------------------------------------------
            echo   AISA Web Automation Task: {seq_no}
            echo --------------------------------------------------
            cd /d "{agent3_dir}"
            echo [1/5] Creating virtual environment...
            "{python_executable}" -m venv env
            echo [2/5] Activating & installing dependencies...
            call "{activate_script}" & pip install --upgrade pip > nul & pip install -r "{reqs_path}"
            if %errorlevel% neq 0 (
                echo.
                echo ########## DEPENDENCY INSTALLATION FAILED ##########
                pause
                exit /b %errorlevel%
            )
            echo [3/5] Installing Playwright browsers...
            playwright install
            if %errorlevel% neq 0 (
                echo.
                echo ########## PLAYWRIGHT BROWSER INSTALLATION FAILED ##########
                pause
                exit /b %errorlevel%
            )
            echo [4/5] Running automation script...
            echo --------------------------------------------------
            python "{script_path}"
            if %errorlevel% equ 0 (echo succeeded > result.txt) else (echo failed > result.txt)
            echo --------------------------------------------------
            echo [5/5] Script finished. This window can be closed.
            pause
            """
            run_script_path = agent3_dir / "run.bat"
            run_script_path.write_text(commands, encoding="utf-8")
            subprocess.Popen(f'start "Web Automation ({seq_no})" cmd /k "{run_script_path}"', shell=True)
        else:  # macOS / Linux
            activate_script = venv_dir / "bin" / "activate"
            commands = f"""#!/bin/bash
            echo "--------------------------------------------------"
            echo "  AISA Web Automation Task: {seq_no}"
            echo "--------------------------------------------------"
            cd "{agent3_dir}"
            echo "[1/5] Creating virtual environment..."
            "{python_executable}" -m venv env
            echo "[2/5] Activating & installing dependencies..."
            source "{activate_script}" && pip install --upgrade pip > /dev/null && pip install -r "{reqs_path}"
            if [ $? -ne 0 ]; then
                echo ""
                echo "########## DEPENDENCY INSTALLATION FAILED ##########"
                read -p "Press Enter to close..."
                exit 1
            fi
            echo "[3/5] Installing Playwright browsers..."
            playwright install
            if [ $? -ne 0 ]; then
                echo ""
                echo "########## PLAYWRIGHT BROWSER INSTALLATION FAILED ##########"
                read -p "Press Enter to close..."
                exit 1
            fi
            echo "[4/5] Running automation script..."
            echo "--------------------------------------------------"
            python "{script_path}"
            if [ $? -eq 0 ]; then echo "succeeded" > result.txt; else echo "failed" > result.txt; fi
            echo "--------------------------------------------------"
            echo "[5/5] Script finished. Press Enter to close."
            read
            """
            run_script_path = agent3_dir / "run.sh"
            run_script_path.write_text(commands, encoding="utf-8")
            os.chmod(run_script_path, 0o755)
            subprocess.Popen(['gnome-terminal', '--title', f'Web Automation ({seq_no})', '--', str(run_script_path)])

    print(f"[{seq_no}] Agent 3 launched execution flow.")
    return {"status": "running"}

