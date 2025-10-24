from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions about dungeons and dragons.',
    instruction='Answer user questions retrieving information about dungeons and dragons from your tools.',
    tools=[MCPToolset(
             connection_params=StdioConnectionParams(
                server_params = StdioServerParameters(
                    command= "node",
                    args= ["dist/index.js"],
                    cwd= "/home/user/telegram-agent/dnd-mcp"
                ),
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']       
    )]
)
