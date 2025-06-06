from mcp.server.fastmcp import FastMCP

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.system_prompt import system_message
import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Draw.io")



@mcp.tool()
def generate_xml(input: str, filename: str = "diagram.drawio", fmt: str = "png") -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", "Based on the {input}, generate xml code for drawio")
    ])

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in environment.")

    llm = ChatGoogleGenerativeAI(
        api_key=api_key,
        model="gemini-2.5-flash-preview-05-20"
    )

    chain: Runnable = prompt | llm
    result = chain.invoke({"input": input})
    xml_content = result.content

    # Save XML to .drawio file
    drawio_path = os.path.expanduser("~/Downloads/diagram.drawio")
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Export to PNG
    export_path = os.path.expanduser("~/Downloads/diagram.png")
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
