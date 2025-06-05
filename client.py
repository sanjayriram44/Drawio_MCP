from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
import asyncio


user_prompt = """
Create a system architecture diagram for an AI Agent Execution Platform, optimized for visual clarity and a black Draw.io background. Follow these structured design requirements:

---

## 🔲 Top-Level Structure
- Enclose the core processing components inside a main bounding box labeled **"ATOMIC AGENT"**.
- This container will hold the full agent execution flow.

---

## 👥 User Access Layer
- Include two user types:
  - **Testing User**
  - **Production User**
- Both users interact with a central **Web App** (UI).

---

## 🧠 Agent Processing Flow (inside "ATOMIC AGENT")
- The **Web App** sends requests to a **Queue Management Service** (Rhombus).
- The queue routes requests to the **Agentic Framework**:
  - Label should mention: *(AutoGen, LangGraph, CrewAI)*.
- The **Agentic Framework** connects to:
  - **Playground** (user-facing agent testing).
  - **Model Selection**
  - **Model Serving**
  - **Redis/Memcache (Caching Service)**

---

## ☁️ Language Models
- **Model Serving** utilizes external LLMs:
  - **Gemini**
  - **Claude**
  - **Databricks/Mistral**
- Use **Cloud shapes** for these models.

---

## 📊 Evaluation & Tracking
- **Model Serving** output flows into an **Evaluation Framework**.
- This then sends data into a **Tracking Service (e.g., MLflow)** (Hexagon).
- Backend tracking database (e.g., PostgreSQL/MongoDB) may be noted, but does not need to be explicitly drawn unless desired.

---

## 📥 RAG Data Pipeline (outside but connected to "ATOMIC AGENT")
- Two data ingestion paths:
  - **Unstructured Data** → **Files API**
  - **Structured Data** → **SQL/DataFrame API**
- Structured data feeds into **Delta Table / Data Products**.
- Unstructured data flows through the **RAG Ingestion Pipeline**, which includes:
  - **Document Loader & Parser**
  - **Text Splitter & Chunker**
  - **Embedding Generator**
- Embeddings are stored in a **Databricks Vector Store**.
- The **Agentic Framework** should connect back to this Vector Store (to enable vector search).

---

## 🔧 Control & Catalog Layer
- **MCP Wrapper (Agent & Function Selector)** connects to:
  - **Agentic Framework**
  - **Agent Registry**
  - **Unity Catalog**
  - **Genie** (rules engine)
  - **Functions (UC Function Calling)**
- **Unity Catalog** also connects to:
  - **Genie**
  - **Functions**
  - A **User Feedback Loop**
  - Placeholder icons for **Models** and **Volume** can be included as internal sub-nodes.

---

## 🧱 Storage Components
- Use **rectangles** for storage components (not cylinders).
  - **Redis/Memcache**
  - **Databricks Vector Store**
  - **Delta Table / Data Products**
- All should have clear labels and be visually distinct.

---

## 🎯 Design Guidelines
- Use left-to-right or top-to-bottom flow.
- Maintain minimum 60px spacing between elements.
- Use consistent shapes:
  - Rectangle for components
  - Rhombus for queues
  - Cloud for LLMs
  - Hexagon for monitoring/logging
- Group related components visually and logically.
- Avoid overlap and clutter.

"""


server_params = StdioServerParameters(
    command = "python",
    args = ["server.py"]
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tool_list = await load_mcp_tools(session)
            tools = {tool.name: tool for tool in tool_list}
            generate_xml = tools["generate_xml"]
            result = await generate_xml.ainvoke({"input": user_prompt})



            print(result)

if __name__ == "__main__":
    asyncio.run(run())
            


