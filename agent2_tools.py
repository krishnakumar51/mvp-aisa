from langchain.tools import tool
from tavily import TavilyClient
import os

@tool
def code_search(query: str) -> str:
    """
    Searches for code snippets and best practices online.
    Use this tool to find examples of how to implement a specific automation task.
    """
    try:
        tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = tavily.search(query=query, search_depth="advanced")
        return "\n".join([f"Source: {r['url']}\n{r['content']}" for r in response['results']])
    except Exception as e:
        return f"Error searching for code: {e}"

@tool
def dependency_suggester(task_description: str) -> str:
    """
    Suggests Python libraries for a given automation task.
    Use this to find the right libraries for the job.
    """
    try:
        tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = tavily.search(query=f"python libraries for {task_description}", search_depth="basic")
        return "\n".join([f"Source: {r['url']}\n{r['content']}" for r in response['results']])
    except Exception as e:
        return f"Error suggesting dependencies: {e}"

@tool
def create_todo_list(task_description: str) -> str:
    """
    Creates a step-by-step TODO list for implementing an automation script.
    Use this to break down the task into smaller, manageable steps.
    """
    return (
        "TODO List:\n"
        "1. Understand the goal of the automation.\n"
        "2. Identify the target application and platform.\n"
        "3. List the main steps from the blueprint.\n"
        "4. For each step, identify the action and target element.\n"
        "5. Write the code for each step, using the appropriate framework.\n"
        "6. Add error handling and logging.\n"
        "7. Create the requirements.txt file.\n"
    )
