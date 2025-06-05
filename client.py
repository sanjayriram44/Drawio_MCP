import streamlit as st
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

st.title("DrawIO PNG Generator")

user_prompt = st.text_input("Enter a detailed prompt to generate a drawio-based PNG...")


if user_prompt:
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    async def call_mcp(prompt):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tool_list = await load_mcp_tools(session)
                tools = {tool.name: tool for tool in tool_list}
                generate_xml = tools["generate_xml"]
                result = await generate_xml.ainvoke({"input": prompt})
                return result

   
    result = asyncio.run(call_mcp(user_prompt))

    
    if result and isinstance(result, str):
        st.success("Diagram successfully generated!")
        st.write(f"Saved to: `{result}`")
    else:
        st.error("Something went wrong generating the diagram.")
