from mcp.server.fastmcp import FastMCP
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph,START, END
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate,HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.system_prompt import system_message
from langchain_groq import ChatGroq
import subprocess
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import json

load_dotenv()
import json

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


@dataclass
class WorkflowState:
    xml_code: str = None
    user_prompt: str = None
    code_instructions: str = None
    is_valid: bool = None
    
graph_builder = StateGraph(WorkflowState)
    
mcp = FastMCP('DrawIO')


def genrate_plan_node(state: WorkflowState):
    llm = ChatGroq(model = "meta-llama/llama-4-maverick-17b-128e-instruct")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("""You are the first node in a chain of xml generating system. simplify the users input into structured
                                    instructions for the next nodes to generate code in an easy and detailed way dont make mistakes."""),
        HumanMessagePromptTemplate.from_template("Based on {user_prompt} generate clear and detailed instructions to generate xml code for the users workflow.")
    ])
    generate_plan_agent = create_react_agent(prompt, llm, state_schema= WorkflowState)
    state.code_instructions = generate_plan_agent.invoke({"user_prompt":state.user_prompt})
    return state

def generate_code_node(state: WorkflowState):
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", "Based on the {input}, generate xml code for drawio")
    ])
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20"
    )
    generate_code_agent = create_react_agent(llm, prompt, state_schema=WorkflowState)
    state.xml_code = generate_code_agent.invoke({"input": state.code_instructions})
    return state


def verify_code_node(state: WorkflowState):
    llm = ChatGroq(model = "llama-3.1-8b-instant")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("You are an xml verifying agent for drawio files. make sure  that the xml code obeys xml and drawio rules. Return true if its valid else return false."),
        HumanMessagePromptTemplate.from_template(
    "Verify the following XML:\n\n{input}\n\nReturn true if valid, else return false."
)

    ])
    verify_code_agent = create_react_agent(llm,prompt, state_schema=WorkflowState)
    
    result = verify_code_agent.invoke({"input": state.xml_code})
    state.is_valid = result.strip().lower() == "true"
    return state


def check_valid(state: WorkflowState):
    return state.is_valid 




graph_builder.add_node("generate_plan", genrate_plan_node)
graph_builder.add_node("generate_code", generate_code_node)
graph_builder.add_node("verify_code", verify_code_node)

graph_builder.add_edge(START, "generate_plan")
graph_builder.add_edge("generate_plan", "generate_code")
graph_builder.add_conditional_edges("verify_code", lambda state: state.is_valid, {True: END, False: "generate_code"})


@mcp.tool
def generate_xml(input: str, filename: str = "diagram.drawio", fmt: str = "png") -> str:
   
    state = WorkflowState()
    state.user_prompt = input   
    graph = graph_builder.compile()
    result = graph.invoke(state)
    xml_content = result.xml_code

    
    drawio_path = os.path.expanduser(f"~/Downloads/{filename}")
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    
    export_path = os.path.expanduser(f"~/Downloads/{filename.replace('.drawio', '.png')}")
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

    
    
    