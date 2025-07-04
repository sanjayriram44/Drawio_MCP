import streamlit as st
import asyncio
import json
import os
import uuid
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
import traceback

st.set_page_config(layout="wide")
st.title("DrawIO Diagram Generator")

if user_prompt := st.chat_input("Describe what you want to add to the diagram..."):
    st.chat_message("human").write(user_prompt)

    async def call_mcp(prompt):
        async with streamablehttp_client("http://127.0.0.1:8000/mcp/") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tool_list = await load_mcp_tools(session)
                tools = {tool.name: tool for tool in tool_list}

                generate_xml = tools["generate_xml"]
                filename = f"diagram_{uuid.uuid4().hex[:8]}"
                
                return await generate_xml.ainvoke({
                    "input": prompt,
                    "filename": filename
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

        drawio_path = data.get("drawio_path")
        st.chat_message("ai").write("Your diagram has been generated and saved to your Downloads folder.")


    except Exception as e:
        st.error("Failed to process result:")
        st.text(str(e))
        st.text(traceback.format_exc())
