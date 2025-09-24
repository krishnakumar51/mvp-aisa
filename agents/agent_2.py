from pathlib import Path
import json
from fastapi import HTTPException
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic

from agent2_tools import code_search, dependency_suggester, create_todo_list

# --- Agent 2's Core Logic (Now with LangChain) ---

def run_agent2(seq_no: str, task_dir: Path, blueprint: dict) -> dict:
    """
    Agent 2: Generates a runnable automation script using a LangChain agent
    with powerful tools.
    """
    print(f"[{seq_no}] Running Agent 2: LangChain-Powered Code Generation")
    out_dir = task_dir / "agent2"
    out_dir.mkdir(parents=True, exist_ok=True)

    platform = blueprint.get("summary", {}).get("platform", "web")
    framework = "Appium" if platform == "mobile" else "Playwright"

    # 1. Initialize the LLM (Groq with Anthropic fallback)
    try:
        llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")
    except Exception:
        llm = ChatAnthropic(model="claude-3-haiku-20240307")

    # 2. Define the tools for the agent
    tools = [code_search, dependency_suggester, create_todo_list]

    # 3. Create the prompt template
    prompt_template = """
    You are a world-class automation script developer. Your goal is to write a high-quality, runnable Python script based on a blueprint.

    **Framework:** {framework}

    **Blueprint:**
    {blueprint}

    **Instructions:**
    1.  First, use the `create_todo_list` tool to outline the steps you will take.
    2.  If you are unsure about how to implement a specific step, use the `code_search` tool to find examples.
    3.  If you need to identify the correct libraries for the task, use the `dependency_suggester` tool.
    4.  Once you have a clear plan, write the complete Python script and the corresponding `requirements.txt` content.
    5.  Your final answer MUST be a JSON object with two keys: "script" and "requirements".

    **Begin!**

    {agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(prompt_template)

    # 4. Create the agent and agent executor
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 5. Run the agent
    try:
        response = agent_executor.invoke({
            "framework": framework,
            "blueprint": json.dumps(blueprint, indent=2),
        })

        # The response from the agent should be a JSON string.
        # We need to parse it to get the script and requirements.
        response_json = json.loads(response["output"])
        
        script_code = response_json.get("script")
        requirements = response_json.get("requirements")

        if not script_code or not requirements:
            raise ValueError("LLM response did not contain 'script' or 'requirements' keys.")

        script_path = out_dir / "automation_script.py"
        reqs_path = out_dir / "requirements.txt"

        script_path.write_text(script_code, encoding="utf-8")
        reqs_path.write_text(requirements, encoding="utf-8")

        print(f"[{seq_no}] Agent 2 finished successfully. Script generated at {script_path}")
        return {"script": str(script_path), "requirements": str(reqs_path)}

    except Exception as e:
        print(f"[{seq_no}] Agent 2 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 2 (Code Gen) failed: {e}")
