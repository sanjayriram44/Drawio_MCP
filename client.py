import streamlit as st
import asyncio
import json
import os
import uuid
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.stdio import stdio_client
import traceback


st.set_page_config(layout="wide")
st.title("DrawIO PNG Generator")

server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

if user_prompt := st.chat_input("Describe what you want to add to the diagram..."):
    st.chat_message("human").write(user_prompt)

    async def call_mcp(prompt):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tool_list = await load_mcp_tools(session)
                tools = {tool.name: tool for tool in tool_list}
                generate_xml = tools["generate_xml"]
                filename = f"diagram_{uuid.uuid4().hex[:8]}"
                return await generate_xml.ainvoke({
                    "input": prompt,
                    "filename": filename,
                    "fmt": "png"
                })

    try:
        result = asyncio.run(call_mcp(user_prompt))

        print("=== Raw result from MCP ===")
        print(result)
        print("===========================")

        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            st.error("Invalid response from server. Not JSON.")
            st.text(result)
            st.stop()

        if "error" in data:
            st.error(f"Tool Error: {data['error']}")
            st.text(json.dumps(data, indent=2))
            st.stop()

        png_path = data.get("png_path")
        drawio_path = data.get("drawio_path")

        st.chat_message("ai").write("Diagram updated based on your input.")

        if png_path and os.path.exists(png_path):
            st.image(png_path, caption="Updated Diagram")
        else:
            st.warning("PNG export failed or missing.")

        if drawio_path and os.path.exists(drawio_path):
            with open(drawio_path, "rb") as f:
                drawio_bytes = f.read()
            st.download_button(
                label="Download .drawio file",
                data=drawio_bytes,
                file_name=os.path.basename(drawio_path),
                mime="application/xml"
            )
        else:
            st.warning("Could not find .drawio file.")

    except Exception as e:
        st.error("Failed to process result:")
        st.text(str(e))
        st.text(traceback.format_exc())
