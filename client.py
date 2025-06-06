import streamlit as st
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from langchain_community.chat_message_histories import StreamlitChatMessageHistory 
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

st.title("DrawIO PNG Generator")

history = StreamlitChatMessageHistory(key = "DrawIO")

for msg in history.messages:
    st.chat_message(msg.type).write(msg.content)
    


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
                result = await generate_xml.ainvoke({"input": prompt})
                return result
            
    context  = "\n".join([m.content for m in history.messages[-5:] if m.type == "human"])
    full_prompt = context + "\n" + user_prompt
            
    

    result = asyncio.run(call_mcp(full_prompt))

    try:
        data = json.loads(result)
        png_path = data.get("png_path")
        drawio_path = data.get("drawio_path")

        
        response_msg = "Diagram updated based on your input."
        history.add_user_message(user_prompt)
        history.add_ai_message(response_msg)

        st.chat_message("ai").write(response_msg)

        if png_path and os.path.exists(png_path):
            st.image(png_path, caption="Updated Diagram")

        if drawio_path and os.path.exists(drawio_path):
            with open(drawio_path, "rb") as f:
                drawio_bytes = f.read()
            st.download_button(
                label="Download .drawio file",
                data=drawio_bytes,
                file_name="diagram.drawio",
                mime="application/xml"
            )
        else:
            st.warning("Could not find .drawio file.")
    except Exception as e:
            st.error(f"Failed to process result: {e}")
