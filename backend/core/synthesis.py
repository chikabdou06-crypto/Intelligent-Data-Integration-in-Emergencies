import json
import re
from datetime import datetime
from backend.core.llm import LLMClient
from backend.core.prompts import get_synthesis_prompt

def generate_synthesis(prompt: str, executed_plan: list) -> str:
    """
    Synthesizes the results of all executed tools into a final polished markdown response.
    """
    # Fast-path for general conversational queries (no data tools called)
    if all(s.get("tool") == "general" for s in executed_plan):
        short_prompt = (
            "You are an intelligent Multi-Tool RAG Assistant for the Comunitat Valenciana and Spain, specializing in municipal data, economics, demographics, emergency response, and natural hazards.\n"
            f"Respond politely and concisely to the user's message in character.\n"
            f"User message: \"{prompt}\"\nResponse:"
        )
        llm = LLMClient(role="synthesizer", temperature=0.5)
        reply = llm.generate(short_prompt).strip()
        reply = re.sub(r'<thinking>.*?</thinking>\s*', '', reply, flags=re.DOTALL)
        return reply or "Hello! I am your Comunitat Valenciana Multi-Tool RAG Assistant. How can I assist you today?"


    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    executed_plan_json = json.dumps(executed_plan, indent=2)
    synthesis_prompt = get_synthesis_prompt(current_date, prompt, executed_plan_json)

    llm = LLMClient(role="synthesizer", temperature=0.3) # Slightly higher temp for better formatting
    reply = llm.generate(synthesis_prompt).strip()
    
    # Strip out the <thinking> block if the model generated one
    reply = re.sub(r'<thinking>.*?</thinking>\s*', '', reply, flags=re.DOTALL)
    
    if not reply:
        return "I encountered an error synthesizing the data. Please check the backend logs."
        
    return reply.strip()
