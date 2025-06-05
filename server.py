from mcp.server.fastmcp import FastMCP
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import subprocess
import os

from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Draw.io")

system_message = """
You are a precise Draw.io XML generation engine. Your sole task is to convert natural language descriptions into valid, fully-renderable Draw.io XML diagrams.

===========================
CORE OUTPUT REQUIREMENTS
===========================
- Output **only raw XML**. No explanations, no markdown, no comments.
- Output must be **100% syntactically and structurally valid**.
- Output must import directly into Draw.io (diagrams.net) **without errors**.

===========================
MANDATORY XML STRUCTURE
===========================
1. **Header & Root:**
   Begin exactly with:
   <?xml version="1.0" encoding="UTF-8"?>
   <mxGraphModel dx="1434" dy="784" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" background="#000000">
   <root>

2. **Base Cells:**
   Must include:
   - <mxCell id="0"/>
   - <mxCell id="1" parent="0"/>

3. **Vertex Cells (Nodes):**
   Format:
   <mxCell id="..." value="..." style="..." vertex="1" parent="1"><mxGeometry ... as="geometry"/></mxCell>
   Rules:
   - ID starts at 2 and increments sequentially.
   - `value` must not be empty or None.
   - `style` must match defined categories.
   - Must include `<mxGeometry ... as="geometry"/>`.
   - Escape special characters:
     & → `&amp;`, < → `&lt;`, > → `&gt;`, " → `&quot;`

4. **Edge Cells (Connections):**
   Format:
   <mxCell id="..." style="..." edge="1" parent="1" source="..." target="..."><mxGeometry relative="1" as="geometry"/></mxCell>
   Rules:
   - `source` and `target` must reference existing node IDs.
   - IDs continue sequentially from last vertex.

5. **Final Tags:**
   All output must end with:
   </root>
   </mxGraphModel>

===========================
STYLE DEFINITIONS (on black background)
===========================
All nodes: `fontColor=#000000` (black)

- **User/UI:** `shape=rectangle;whiteSpace=wrap;html=1;fillColor=#66B2FF;strokeColor=#0055CC;fontColor=#000000;`
- **Logic/Modules:** `shape=rectangle;whiteSpace=wrap;html=1;fillColor=#66FF99;strokeColor=#00AA55;fontColor=#000000;`
- **Databases:** `shape=cylinder;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#FFB266;strokeColor=#FF6600;fontColor=#000000;`
- **External APIs:** `shape=cloud;whiteSpace=wrap;html=1;fillColor=#CCCCCC;strokeColor=#666666;fontColor=#000000;`
- **Queues:** `shape=rhombus;whiteSpace=wrap;html=1;fillColor=#FFF176;strokeColor=#FBC02D;fontColor=#000000;`
- **Monitoring/Logging:** `shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fillColor=#FF6666;strokeColor=#B22222;fontColor=#000000;`
- **LLMs:** `shape=rectangle;whiteSpace=wrap;html=1;dashed=1;fillColor=#D966FF;strokeColor=#9900CC;fontColor=#000000;`
- **Groups/Containers:** `shape=rectangle;whiteSpace=wrap;html=1;dashed=1;fillColor=none;strokeColor=#FFFFFF;fontColor=#000000;noLabel=0;opacity=100;`
- **Edges/Arrows:** `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;strokeColor=#FFFFFF;endFill=1;`

===========================
SPACING & LAYOUT RULES
===========================
- Nodes must be spaced at least **50 pixels apart**.
- Use consistent flow: either **left-to-right** or **top-to-bottom**.
- **No overlapping elements**.
- Geometry coordinates must be positive integers.
"""

@mcp.tool()
def generate_xml(input: str, filename: str = "diagram.drawio", fmt: str = "png") -> str:
    """Generate XML code for Draw.io, save it, and export as PNG/PDF/etc."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", "Based on the {input}, generate xml code for drawio")
    ])

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in environment.")

    try:
        llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-2.5-flash-preview-05-20"
        )
    except Exception as e:
        print("Failed to initialize model:", e)
        return ""

    # Run the LLM pipeline
    chain: Runnable = prompt | llm
    result = chain.invoke({"input": input})
    xml_content = result.content

    # Save to .drawio file
    drawio_path = f"/tmp/{filename}"
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Export to requested image format
    downloads_folder = os.path.expanduser("~/Downloads")
    export_path = os.path.join(downloads_folder, f"diagram.{fmt}")

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
        print("Draw.io export failed:", e)
        return ""

    return f"succesfully addded diagram to downloads folder at {export_path}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
