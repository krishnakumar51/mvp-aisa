import re
import json
from fastapi import HTTPException
from config import anthropic_client, groq_client

def get_llm_response(prompt: str, system_prompt: str) -> str:
    """
    Gets a response from an LLM, trying Groq first and falling back to Anthropic.
    """
    # Priority 1: Groq
    if groq_client:
        try:
            print("--- Calling Groq API (Primary) ---")
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model="openai/gpt-oss-20b",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API failed: {e}. Falling back to Anthropic.")

    # Priority 2: Anthropic (Fallback)
    if anthropic_client:
        try:
            print("--- Calling Anthropic API (Fallback) ---")
            message = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Anthropic API also failed: {e}")
            raise HTTPException(status_code=500, detail="Both LLM providers failed.")

    raise HTTPException(status_code=500, detail="No LLM providers are configured.")

def extract_json_from_response(text: str) -> dict:
    """
    Extracts JSON content robustly from an LLM response by finding the
    outermost curly braces.
    """
    start_brace = text.find('{')
    end_brace = text.rfind('}')
    if start_brace == -1 or end_brace == -1:
        raise ValueError("No valid JSON object found in the LLM response.")
    
    json_text = text[start_brace:end_brace+1]
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response: {e}")
        print(f"Attempted to parse text: {json_text}")
        raise ValueError("LLM did not return valid JSON.")