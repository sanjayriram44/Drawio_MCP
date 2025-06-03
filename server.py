from mcp.server.fastmcp import FastMCP
from langchain_groq import ChatGroq
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("Draw.io")

@mcp.tool()
def generate_xml(input: str) -> str:
    """Generate XML code for Draw.io"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpfule assitant that converst user input into XML format for Drawio"),
        ("user", "Based on the {input}, generate xml code for drawio")
    ])
    
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model = "llama-3.3-70b-versatile")
    chain: Runnable = prompt | llm
    result = chain.invoke({"input":input})
    return result.content


if __name__ == "__main__":
    mcp.run(transport="stdio")

    