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
st.title("DrawIO PNG Generator")

if user_prompt := st.chat_input("Describe what you want to add to the diagram..."):
    st.chat_message("human").write(user_prompt)

    async def call_mcp(prompt):
        # Connect to the MCP server using streamable HTTP client
        async with streamablehttp_client("http://127.0.0.1:8000/mcp/") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()  # Initialize the session with the server
                
                # Load available tools from the server
                tool_list = await load_mcp_tools(session)
                tools = {tool.name: tool for tool in tool_list}

                # Use the generate_xml tool from the list
                generate_xml = tools["generate_xml"]
                filename = f"diagram_{uuid.uuid4().hex[:8]}"
                
                # Call the tool to generate the diagram
                return await generate_xml.ainvoke({
                    "input": prompt,
                    "filename": filename,
                    "fmt": "png"
                })

    try:
        # Run the asynchronous function
        result = asyncio.run(call_mcp(user_prompt))

        print("=== Raw result from MCP ===")
        print(result)
        print("===========================")

        try:
            # Parse the result from the server (expected to be JSON)
            data = json.loads(result)
        except json.JSONDecodeError:
            st.error("Invalid response from server. Not JSON.")
            st.text(result)
            st.stop()

        # Check if there is any error in the response
        if "error" in data:
            st.error(f"Tool Error: {data['error']}")
            st.text(json.dumps(data, indent=2))
            st.stop()

        png_path = data.get("png_path")
        drawio_path = data.get("drawio_path")

        st.chat_message("ai").write("Diagram updated based on your input.")

        # Display the generated PNG diagram
        if png_path and os.path.exists(png_path):
            st.image(png_path, caption="Updated Diagram")
        else:
            st.warning("PNG export failed or missing.")

        # Allow user to download the .drawio file
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
