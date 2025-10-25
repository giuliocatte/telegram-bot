from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

async def get_agent_async():
  """Creates an ADK Agent equipped with tools from the MCP Server."""
  toolset = MCPToolset(
             connection_params=StdioConnectionParams(
                server_params = StdioServerParameters(
                    command= "node",
                    args= ["dist/index.js"],
                    cwd= "/home/user/telegram-agent/dnd-mcp"
                ),
            ))

  # Use in an agent
  root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions about dungeons and dragons.',
    instruction='Answer user questions retrieving information about dungeons and dragons from your tools.',
    tools=[toolset], # Provide the MCP tools to the ADK agent
  )
  return root_agent, toolset
