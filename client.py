from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
import asyncio


user_prompt = """
I want to design a system architecture for an e-commerce platform.

The system should include:

- A web frontend that users interact with, built in React.
- A mobile app (iOS + Android) that communicates with the backend via an API gateway.
- An API gateway that routes traffic to different backend services.
- A set of microservices for:
    - User management
    - Product catalog
    - Order processing
    - Payment service
    - Notification service (email + SMS)

All services should communicate via REST APIs.

The services should publish logs to a centralized logging system (like ELK), and send metrics to a monitoring stack (like Prometheus + Grafana).

There should be a PostgreSQL database for user and order data, and a MongoDB instance for product catalog data.

Payments should be processed via an external payment gateway (Stripe).

I also want to include a message queue (RabbitMQ) between the order processing and notification service for async communication.

Please create a system diagram showing all components, how they connect, and include labels for services and data flow.
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
            


