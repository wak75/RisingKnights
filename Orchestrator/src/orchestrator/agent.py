"""Orchestrator Agent definition using Google ADK."""

import asyncio
from typing import Optional, List, Dict, Any

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams, StreamableHTTPConnectionParams
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .config import config, OrchestratorConfig, MCPServerConfig
from .session_store import session_store, SessionData


# Callback for streaming tool calls
from typing import Callable

ToolCallCallback = Callable[[str, Dict[str, Any]], None]


class OrchestratorAgent:
    """
    Orchestrator Agent that coordinates multiple MCP servers.
    
    This agent uses Google ADK with Gemini model to intelligently
    orchestrate tools from various MCP servers (Jenkins, Kubernetes, etc.).
    
    Features:
    - Parallel RCA: For generic troubleshooting, queries all MCP servers in parallel
    - Platform-specific: For targeted queries, uses only relevant MCP tools
    - Tool call streaming: Real-time visibility into which tools are being called
    """
    
    def __init__(self, orchestrator_config: Optional[OrchestratorConfig] = None):
        """Initialize the Orchestrator Agent."""
        self.config = orchestrator_config or config
        self.agent: Optional[Agent] = None
        self.session_service = InMemorySessionService()
        self.mcp_toolsets: Dict[str, McpToolset] = {}  # name -> toolset
        self.sub_agents: Dict[str, Agent] = {}  # name -> specialized agent
        self.parallel_rca_agent: Optional[ParallelAgent] = None
        self.tool_call_callback: Optional[ToolCallCallback] = None  # For streaming tool calls
    
    async def initialize(self) -> None:
        """Initialize the agent with MCP tools and sub-agents."""
        # Load tools from all enabled MCP servers
        await self._load_mcp_tools()
        
        # Create specialized sub-agents for each MCP server (for parallel RCA)
        await self._create_sub_agents()
        
        # Collect ALL tools for the main orchestrator
        all_tools = []
        for toolset in self.mcp_toolsets.values():
            tools = await toolset.get_tools()
            all_tools.extend(tools)
        
        # Create the main orchestrator agent (with all tools)
        self.agent = Agent(
            name=self.config.agent_name,
            model=self.config.model_name,
            description=self.config.agent_description,
            instruction=self._build_instruction(),
            tools=all_tools if all_tools else None,
        )
        
        # Create parallel RCA agent (sub-agents run in parallel)
        if len(self.sub_agents) > 1:
            self.parallel_rca_agent = ParallelAgent(
                name="parallel_rca_agent",
                description="Runs RCA investigation across all platforms in parallel",
                sub_agents=list(self.sub_agents.values())
            )
    
    async def _load_mcp_tools(self) -> None:
        """Load tools from all enabled MCP servers."""
        enabled_servers = self.config.get_enabled_servers()
        
        for server_config in enabled_servers:
            try:
                toolset = await self._connect_mcp_server(server_config)
                self.mcp_toolsets[server_config.name] = toolset
                tools = await toolset.get_tools()
                print(f"✓ Connected to MCP server: {server_config.name} ({len(tools)} tools)")
            except Exception as e:
                print(f"✗ Failed to connect to MCP server {server_config.name}: {e}")
    
    async def _create_sub_agents(self) -> None:
        """Create specialized sub-agents for each MCP server."""
        for server_name, toolset in self.mcp_toolsets.items():
            try:
                tools = await toolset.get_tools()
                server_config = next(
                    (s for s in self.config.get_enabled_servers() if s.name == server_name), 
                    None
                )
                
                # Create a specialized agent for this MCP server
                sub_agent = Agent(
                    name=f"{server_name}_agent",
                    model=self.config.model_name,
                    description=f"Specialized agent for {server_name}: {server_config.description if server_config else ''}",
                    instruction=self._build_sub_agent_instruction(server_name, server_config),
                    tools=tools,
                )
                self.sub_agents[server_name] = sub_agent
                print(f"✓ Created sub-agent for {server_name}")
            except Exception as e:
                print(f"✗ Failed to create sub-agent for {server_name}: {e}")
    
    def _build_sub_agent_instruction(self, server_name: str, server_config: Optional[MCPServerConfig]) -> str:
        """Build instruction for a specialized sub-agent."""
        description = server_config.description if server_config else ""
        
        return f"""You are a specialized {server_name.upper()} investigation agent.

Your role: Investigate issues and perform Root Cause Analysis (RCA) using {server_name} tools.
Capabilities: {description}

## Investigation Protocol for {server_name.upper()}

1. **Gather Evidence**: Use your tools to collect relevant logs, events, statuses
2. **Analyze**: Look for errors, warnings, anomalies
3. **Identify Root Cause**: Determine what's causing the issue
4. **Report Findings**: Summarize what you found with specific details

## Output Format
Always structure your findings as:

**🔍 {server_name.upper()} Investigation Report**

**Status**: [✅ No Issues / ⚠️ Issues Found / ❌ Critical Issues]

**Evidence Collected**:
- List what you checked

**Findings**:
- Describe what you found

**Root Cause** (if identified):
- Specific cause of the issue

**Recommendations**:
- Suggested actions to fix
"""

    async def _connect_mcp_server(self, server_config: MCPServerConfig) -> McpToolset:
        """Connect to a single MCP server and return the toolset."""
        if server_config.transport == "sse":
            connection_params = SseConnectionParams(url=server_config.url)
            toolset = McpToolset(connection_params=connection_params)
            return toolset
        elif server_config.transport in ("http", "streamable-http"):
            # HTTP transport for remote MCP servers (like GitHub)
            connection_params = StreamableHTTPConnectionParams(
                url=server_config.url,
                headers=server_config.headers if server_config.headers else None
            )
            toolset = McpToolset(connection_params=connection_params)
            return toolset
        else:
            raise ValueError(f"Unsupported transport: {server_config.transport}")
    
    def _build_instruction(self) -> str:
        """Build the instruction prompt for the main orchestrator agent."""
        server_names = [s.name for s in self.config.get_enabled_servers()]
        server_descriptions = "\n".join([
            f"- **{s.name}**: {s.description}"
            for s in self.config.get_enabled_servers()
        ])
        
        mcp_section = ""
        if server_descriptions:
            mcp_section = f"""

## Available MCP Tools
You have access to the following MCP (Model Context Protocol) servers:
{server_descriptions}

## Intelligent Query Routing

### Platform-Specific Queries
When the user mentions a SPECIFIC platform (Jenkins, Kubernetes, etc.), use only that platform's tools:
- "Jenkins build is failing" → Use ONLY Jenkins tools
- "Kubernetes pod is crashing" → Use ONLY k8s_* tools
- "Check Jenkins job status" → Use ONLY Jenkins tools

### Generic/Ambiguous Queries (PARALLEL RCA)
When the user describes a GENERIC issue without specifying a platform:
- "Deployment is failing" → Investigate BOTH Jenkins AND Kubernetes
- "Something is broken" → Check ALL available platforms
- "Why isn't my app working?" → Query ALL MCP servers

For generic issues, I will investigate ALL platforms ({', '.join(server_names)}) to find the root cause.

## Root Cause Analysis (RCA) Protocol

When investigating issues:
1. **Identify Scope**: Is this platform-specific or generic?
2. **Gather Evidence**: Collect logs, events, statuses from relevant platforms
3. **Cross-Reference**: For generic issues, compare findings across platforms
4. **Identify Root Cause**: Determine the actual cause
5. **Recommend Actions**: Suggest specific fixes

## Handling Typos and Ambiguous Names
When a resource name doesn't exist:
1. List all available resources to find similar names
2. Ask: "Did you mean 'X'? I found a similar name."
3. Wait for confirmation before proceeding
"""
        
        return f"""You are a helpful, intelligent AI assistant and DevOps expert. You can answer general questions, help with coding, explain concepts, and have conversations on any topic.

{mcp_section}

## Guidelines
- Be helpful, accurate, and informative
- For general questions, answer directly using your knowledge
- For infrastructure/DevOps tasks, use the appropriate MCP tools

## Output Formatting (IMPORTANT)
When presenting data from tools, ALWAYS format it in a human-readable way:

1. **For lists of resources (pods, deployments, jobs, etc.):**
   - Use clear headers and sections
   - Group by namespace when showing Kubernetes resources
   - Use status indicators: ✅ (healthy/running), ⚠️ (warning), ❌ (error/failed)
   - Show only the most relevant information, not raw JSON

2. **For RCA/Investigation Results:**
   - Start with overall status (✅ / ⚠️ / ❌)
   - List evidence collected from each platform
   - Clearly state the root cause
   - Provide actionable recommendations

3. **Never output raw JSON** - always transform into readable text.

You are capable of:
- Answering general knowledge questions
- Helping with coding and technical questions
- Managing Jenkins jobs, builds, and pipelines
- Managing Kubernetes resources (pods, deployments, services, etc.)
- Cross-platform Root Cause Analysis
- System administration tasks
"""
    
    def _is_platform_specific_query(self, query: str) -> Optional[str]:
        """
        Determine if a query is platform-specific.
        
        Returns the platform name if specific, None if generic.
        """
        query_lower = query.lower()
        
        # Jenkins indicators
        jenkins_keywords = ['jenkins', 'pipeline', 'build job', 'jenkins job', 'jenkinsfile', 'ci/cd pipeline']
        for kw in jenkins_keywords:
            if kw in query_lower:
                return 'jenkins'
        
        # Kubernetes indicators
        k8s_keywords = ['kubernetes', 'k8s', 'pod', 'deployment', 'kubectl', 'namespace', 'container', 'helm', 'kube']
        for kw in k8s_keywords:
            if kw in query_lower:
                return 'kubernetes'
        
        return None
    
    def _is_rca_query(self, query: str) -> bool:
        """Determine if this is an RCA/troubleshooting query."""
        rca_indicators = [
            'failing', 'failed', 'error', 'broken', 'not working', 'issue', 'problem',
            'why', 'debug', 'troubleshoot', 'investigate', 'rca', 'root cause',
            'crashing', 'down', 'unavailable', 'timeout', 'stuck', 'help'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in rca_indicators)
    
    async def chat(
        self,
        user_input: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "orchestrator",
        save_to_store: bool = True
    ) -> str:
        """
        Send a message to the orchestrator agent and get a response.
        
        For generic RCA queries, uses parallel execution across all MCP servers.
        For platform-specific queries, uses only relevant tools.
        """
        if self.agent is None:
            await self.initialize()
        
        # Save user message to persistent store
        if save_to_store:
            session_store.add_message(session_id, "user", user_input, user_id)
        
        # Determine query type
        specific_platform = self._is_platform_specific_query(user_input)
        is_rca = self._is_rca_query(user_input)
        
        # Use parallel RCA for generic troubleshooting queries
        if is_rca and specific_platform is None and self.parallel_rca_agent and len(self.sub_agents) > 1:
            print(f"🔄 Using PARALLEL RCA across {len(self.sub_agents)} platforms...")
            response = await self._parallel_rca(user_input, user_id, session_id, app_name)
        else:
            # Use main orchestrator for everything else
            if specific_platform:
                print(f"🎯 Platform-specific query: {specific_platform}")
            response = await self._single_agent_chat(user_input, user_id, session_id, app_name)
        
        # Save assistant response to persistent store
        if save_to_store:
            session_store.add_message(session_id, "assistant", response, user_id)
        
        return response
    
    async def _single_agent_chat(
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        app_name: str
    ) -> str:
        """Standard single-agent chat."""
        response_parts = []
        async for event_type, event_data in self._single_agent_chat_stream(
            user_input, user_id, session_id, app_name
        ):
            if event_type == "response":
                response_parts.append(event_data)
        return "".join(response_parts) if response_parts else "No response from agent."
    
    async def _single_agent_chat_stream(
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        app_name: str
    ):
        """Stream single-agent chat with tool call events."""
        # Ensure ADK session exists
        try:
            await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            pass
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )
        
        runner = Runner(
            agent=self.agent,
            app_name=app_name,
            session_service=self.session_service
        )
        
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                # Check for function calls (tool calls)
                if event.content is not None and hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        # Handle function call parts
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            tool_name = func_call.name if hasattr(func_call, 'name') else str(func_call)
                            args = func_call.args if hasattr(func_call, 'args') else {}
                            yield ("tool_call", {"name": tool_name, "args": dict(args) if args else {}})
                
                # Final response
                if event.is_final_response():
                    if event.content is not None and hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                yield ("response", part.text)
        except Exception as e:
            print(f"Error during agent execution: {e}")
            yield ("error", str(e))
    
    async def chat_stream(
        self,
        user_input: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "orchestrator",
        save_to_store: bool = True
    ):
        """
        Stream chat with tool call events.
        
        Yields tuples of (event_type, event_data):
        - ("status", message): Status updates
        - ("tool_call", {"name": str, "args": dict}): Tool being called
        - ("response", text): Final response text
        - ("error", message): Error messages
        """
        if self.agent is None:
            await self.initialize()
        
        # Save user message to persistent store
        if save_to_store:
            session_store.add_message(session_id, "user", user_input, user_id)
        
        # Determine query type
        specific_platform = self._is_platform_specific_query(user_input)
        is_rca = self._is_rca_query(user_input)
        
        response_parts = []
        
        # Use parallel RCA for generic troubleshooting queries
        if is_rca and specific_platform is None and self.parallel_rca_agent and len(self.sub_agents) > 1:
            yield ("status", f"🔄 Using PARALLEL RCA across {len(self.sub_agents)} platforms...")
            
            # For parallel RCA, we need to handle differently
            response = await self._parallel_rca(user_input, user_id, session_id, app_name)
            yield ("response", response)
            response_parts.append(response)
        else:
            # Use main orchestrator for everything else
            if specific_platform:
                yield ("status", f"🎯 Platform-specific query: {specific_platform}")
            else:
                yield ("status", "💬 Processing with main agent...")
            
            async for event_type, event_data in self._single_agent_chat_stream(
                user_input, user_id, session_id, app_name
            ):
                yield (event_type, event_data)
                if event_type == "response":
                    response_parts.append(event_data)
        
        # Save assistant response to persistent store
        if save_to_store and response_parts:
            session_store.add_message(session_id, "assistant", "".join(response_parts), user_id)
    
    async def _parallel_rca(
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        app_name: str
    ) -> str:
        """
        Perform parallel RCA across all MCP servers.
        
        Each sub-agent investigates the issue independently and in parallel.
        Results are then combined for a comprehensive RCA report.
        """
        # Create tasks for parallel execution
        tasks = []
        for server_name, sub_agent in self.sub_agents.items():
            task = self._run_sub_agent_rca(
                sub_agent, server_name, user_input, user_id, 
                f"{session_id}_{server_name}", app_name
            )
            tasks.append((server_name, task))
        
        # Run all investigations in parallel
        results = {}
        parallel_tasks = [task for _, task in tasks]
        server_names = [name for name, _ in tasks]
        
        completed = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        
        for server_name, result in zip(server_names, completed):
            if isinstance(result, Exception):
                results[server_name] = f"❌ Error during investigation: {str(result)}"
            else:
                results[server_name] = result
        
        # Combine results into comprehensive RCA report
        combined_report = self._combine_rca_results(user_input, results)
        return combined_report
    
    async def _run_sub_agent_rca(
        self,
        sub_agent: Agent,
        server_name: str,
        user_input: str,
        user_id: str,
        session_id: str,
        app_name: str
    ) -> str:
        """Run RCA investigation using a specific sub-agent."""
        try:
            await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            pass
        
        # Enhance the query for RCA context
        rca_query = f"""Investigate this issue and perform Root Cause Analysis:

{user_input}

Use your tools to:
1. Check relevant logs and events
2. Check resource status and health
3. Look for errors or anomalies
4. Identify potential root causes

Provide a detailed investigation report."""
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=rca_query)]
        )
        
        runner = Runner(
            agent=sub_agent,
            app_name=app_name,
            session_service=self.session_service
        )
        
        response_parts = []
        
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                # Collect all events with content
                if event.content is not None and hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        # Handle text parts
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)
                        # Handle function response parts (tool results)
                        elif hasattr(part, 'function_response') and part.function_response:
                            func_resp = part.function_response
                            if hasattr(func_resp, 'response') and func_resp.response:
                                resp_data = func_resp.response
                                if isinstance(resp_data, dict) and 'result' in resp_data:
                                    response_parts.append(f"\n[Tool Result]\n{resp_data['result']}\n")
                                elif isinstance(resp_data, str):
                                    response_parts.append(f"\n[Tool Result]\n{resp_data}\n")
                
                # For final response, prioritize text content
                if event.is_final_response():
                    break
                    
        except Exception as e:
            return f"Error: {str(e)}"
        
        return "".join(response_parts) if response_parts else "No findings."
    
    def _combine_rca_results(self, original_query: str, results: Dict[str, str]) -> str:
        """Combine RCA results from multiple platforms into a comprehensive report."""
        report_lines = [
            "# 🔍 Parallel Root Cause Analysis Report",
            "",
            f"**Issue**: {original_query}",
            "",
            f"**Platforms Investigated**: {', '.join(results.keys())}",
            "",
            "---",
            ""
        ]
        
        # Add each platform's findings
        for platform, findings in results.items():
            report_lines.append(f"## 📊 {platform.upper()} Investigation")
            report_lines.append("")
            report_lines.append(findings)
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
        
        # Add summary section
        report_lines.append("## 📋 Combined Summary")
        report_lines.append("")
        report_lines.append("Review the findings above from each platform to identify the root cause.")
        report_lines.append("Cross-reference issues that appear in multiple platforms.")
        
        return "\n".join(report_lines)
    
    async def cleanup(self) -> None:
        """Cleanup resources and close MCP connections."""
        for toolset in self.mcp_toolsets.values():
            try:
                toolset.close()
            except Exception as e:
                print(f"Error during cleanup: {e}")
        self.mcp_toolsets.clear()
        self.sub_agents.clear()


# Factory function for creating the agent
async def create_orchestrator_agent(
    orchestrator_config: Optional[OrchestratorConfig] = None
) -> OrchestratorAgent:
    """Create and initialize an orchestrator agent."""
    agent = OrchestratorAgent(orchestrator_config)
    await agent.initialize()
    return agent