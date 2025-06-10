from mcp.server.fastmcp import FastMCP
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.system_prompt import system_message
from dataclasses import dataclass, field
from langchain_groq import ChatGroq
import subprocess
from typing import List, Any
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

@dataclass
class WorkflowState:
    xml_code: str = None
    user_prompt: str = None
    code_instructions: str = None
    messages: List[Any] = field(default_factory=list)

graph_builder = StateGraph(WorkflowState)
mcp = FastMCP('DrawIO')

def generate_plan_node(state: WorkflowState):
    llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            "You are the first node in a chain of xml generating system. Simplify the user's input into structured instructions for the next nodes. Be clear and avoid mistakes."
        ),
        HumanMessagePromptTemplate.from_template(
            "Based on {user_prompt} generate clear and detailed instructions to generate xml code for the user's workflow."
        )
    ])
    chain = prompt | llm
    try:
        result = chain.invoke({"user_prompt": state.user_prompt})
        state.code_instructions = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        print(f"Error in generate_plan_node: {e}")
        state.code_instructions = None
    return state

def generate_code_node(state: WorkflowState):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template(
            "Based on the following input, generate XML code for draw.io:\n\n{input}"
        )
    ])
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20")
    chain = prompt | llm
    try:
        result = chain.invoke({"input": state.code_instructions})
        state.xml_code = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        print(f"Error in generate_code_node: {e}")
        state.xml_code = None
    return state

def verify_code_node(state: WorkflowState):
    llm = ChatGroq(model="llama-3.1-8b-instant")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """You are a fixer agent for Draw.io XML diagrams.

Your job is to take a possibly broken or incomplete XML string that should be used in Draw.io and return a fully corrected and valid XML file.

**Important rules:**
- Only output valid XML — starting with <mxfile> or <mxGraphModel>
- DO NOT add explanations, comments, or markdown
- DO NOT wrap the response in code blocks like ```xml
- DO NOT say anything like "Here is the fixed XML"
- Just return clean, raw XML — nothing else
"""
        ),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = prompt | llm
    try:
        result = chain.invoke({"input": state.xml_code})
        state.xml_code = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        print(f"Error in verify_code_node: {e}")
        state.xml_code = None
    return state

graph_builder.add_node("generate_plan", generate_plan_node)
graph_builder.add_node("generate_code", generate_code_node)
graph_builder.add_node("verify_code", verify_code_node)

graph_builder.add_edge(START, "generate_plan")
graph_builder.add_edge("generate_plan", "generate_code")
graph_builder.add_edge("generate_code", "verify_code")
graph_builder.add_edge("verify_code", END)

@mcp.tool()
def generate_xml(input: str, filename: str = "diagram.drawio", fmt: str = "png") -> str:
    state = WorkflowState(user_prompt=input)
    graph = graph_builder.compile()
    result = graph.invoke(state)

    xml_content = result.get("xml_code") if result else None

    if not xml_content or "<mx" not in xml_content:
        return json.dumps({"error": "Generated XML is invalid or empty"})

    drawio_path = os.path.expanduser(f"~/Downloads/{filename}")
    try:
        with open(drawio_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
    except Exception as e:
        return json.dumps({"error": f"Failed to write .drawio file: {e}"})

    # Slight delay just in case I/O lags
    time.sleep(0.2)

    export_path = drawio_path.replace(".drawio", f".{fmt}")
    if not os.path.exists(drawio_path):
        return json.dumps({"error": "Expected .drawio file not found, export aborted."})

    try:
        subprocess.run([
            "/Applications/draw.io.app/Contents/MacOS/draw.io",
            "-x",
            "-f", fmt,
            "--scale", "2.5",
            "-o", export_path,
            drawio_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Draw.io export failed: {e}"})

    return json.dumps({
        "png_path": export_path,
        "drawio_path": drawio_path
    })

if __name__ == "__main__":
    mcp.run(transport="stdio")
