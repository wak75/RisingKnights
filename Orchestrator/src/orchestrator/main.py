"""Main entry point for the Orchestrator Agent - CLI and Web API."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json as json_lib
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .agent import OrchestratorAgent, create_orchestrator_agent
from .config import config, check_api_key
from .session_store import session_store

# Get the static files directory
STATIC_DIR = Path(__file__).parent / "static"


# Global agent instance for web API
_agent: Optional[OrchestratorAgent] = None
console = Console()


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    user_id: str
    session_id: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model: str
    mcp_servers: list[str]


class SessionSummary(BaseModel):
    """Summary of a session."""
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class SessionDetail(BaseModel):
    """Detailed session with messages."""
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict]


class MessageModel(BaseModel):
    """A conversation message."""
    role: str
    content: str
    timestamp: str


# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize and cleanup agent."""
    global _agent
    console.print("[bold blue]Initializing Orchestrator Agent...[/bold blue]")
    try:
        _agent = await create_orchestrator_agent()
        console.print("[bold green]✓ Orchestrator Agent initialized successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to initialize agent: {e}[/bold red]")
        _agent = None
    
    yield
    
    # Cleanup
    if _agent:
        await _agent.cleanup()
        console.print("[bold blue]Orchestrator Agent cleaned up.[/bold blue]")


app = FastAPI(
    title="Orchestrator Agent API",
    description="Google ADK based orchestrator agent for MCP servers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health status of the orchestrator agent."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return HealthResponse(
        status="healthy",
        model=config.model_name,
        mcp_servers=[s.name for s in config.get_enabled_servers()]
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the orchestrator agent."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    try:
        response = await _agent.chat(
            user_input=request.message,
            user_id=user_id,
            session_id=session_id
        )
        return ChatResponse(
            response=response,
            user_id=user_id,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message to the orchestrator agent with streaming progress and tool call updates."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    async def generate():
        """Generator function for SSE streaming with tool calls."""
        try:
            # Send initial status
            yield f"data: {json_lib.dumps({'type': 'status', 'message': '🔄 Processing your request...'})}\n\n"
            
            response_parts = []
            
            # Stream chat events including tool calls
            async for event_type, event_data in _agent.chat_stream(
                user_input=request.message,
                user_id=user_id,
                session_id=session_id
            ):
                if event_type == "status":
                    yield f"data: {json_lib.dumps({'type': 'status', 'message': event_data})}\n\n"
                
                elif event_type == "tool_call":
                    tool_name = event_data.get('name', 'unknown')
                    tool_args = event_data.get('args', {})
                    # Format tool call message
                    args_preview = ', '.join([f"{k}={repr(v)[:30]}" for k, v in list(tool_args.items())[:3]])
                    message = f"🔧 Calling: {tool_name}({args_preview})"
                    yield f"data: {json_lib.dumps({'type': 'tool_call', 'message': message, 'tool_name': tool_name, 'args': tool_args})}\n\n"
                
                elif event_type == "response":
                    response_parts.append(event_data)
                
                elif event_type == "error":
                    yield f"data: {json_lib.dumps({'type': 'error', 'message': event_data})}\n\n"
            
            # Send final response
            final_response = "".join(response_parts) if response_parts else "No response from agent."
            yield f"data: {json_lib.dumps({'type': 'complete', 'response': final_response, 'user_id': user_id, 'session_id': session_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json_lib.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/servers")
async def list_servers():
    """List all configured MCP servers."""
    return {
        "servers": [
            {
                "name": s.name,
                "url": s.url,
                "transport": s.transport,
                "enabled": s.enabled,
                "description": s.description
            }
            for s in config.mcp_servers
        ]
    }


# ============================================================================
# Session Management API Endpoints
# ============================================================================

@app.get("/sessions", response_model=List[SessionSummary])
async def list_sessions(user_id: Optional[str] = None):
    """List all saved sessions, optionally filtered by user."""
    sessions = session_store.list_sessions(user_id)
    return [
        SessionSummary(
            session_id=s.session_id,
            user_id=s.user_id,
            title=s.title or "Untitled",
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """Get a specific session with all messages."""
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionDetail(
        session_id=session.session_id,
        user_id=session.user_id,
        title=session.title or "Untitled",
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in session.messages
        ]
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    success = session_store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


@app.post("/sessions/{session_id}/resume", response_model=ChatResponse)
async def resume_session(session_id: str, request: ChatRequest):
    """Resume a conversation in an existing session."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        response = await _agent.chat(
            user_input=request.message,
            user_id=session.user_id,
            session_id=session_id
        )
        return ChatResponse(
            response=response,
            user_id=session.user_id,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def serve_ui():
    """Serve the web UI."""
    return FileResponse(STATIC_DIR / "index.html")


# ============================================================================
# CLI Interface
# ============================================================================

async def run_cli():
    """Run the interactive CLI chat interface."""
    console.print(Panel.fit(
        "[bold blue]Orchestrator Agent CLI[/bold blue]\n"
        "An intelligent agent for orchestrating MCP servers\n"
        "Type 'quit' or 'exit' to stop, 'help' for commands",
        title="Welcome",
        border_style="blue"
    ))
    
    # Initialize agent
    console.print("\n[bold]Initializing agent...[/bold]")
    try:
        agent = await create_orchestrator_agent()
        console.print("[bold green]✓ Agent ready![/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to initialize agent: {e}[/bold red]")
        return
    
    # Display connected servers
    enabled_servers = config.get_enabled_servers()
    if enabled_servers:
        console.print("[bold]Connected MCP Servers:[/bold]")
        for server in enabled_servers:
            console.print(f"  • {server.name}: {server.description}")
        console.print()
    
    user_id = f"cli_user_{uuid.uuid4().hex[:8]}"
    session_id = f"cli_session_{uuid.uuid4().hex[:8]}"
    
    console.print(f"[dim]Session ID: {session_id}[/dim]\n")
    
    try:
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            except EOFError:
                break
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[bold]Goodbye![/bold]")
                break
            
            if user_input.lower() == 'help':
                console.print(Panel(
                    "[bold]Available Commands:[/bold]\n"
                    "• [cyan]quit/exit/q[/cyan] - Exit the CLI\n"
                    "• [cyan]help[/cyan] - Show this help message\n"
                    "• [cyan]servers[/cyan] - List connected MCP servers\n"
                    "• [cyan]new[/cyan] - Start a new conversation session\n"
                    "• [cyan]sessions[/cyan] - List all saved sessions\n"
                    "• [cyan]load <session_id>[/cyan] - Load and resume a session\n"
                    "• [cyan]history[/cyan] - Show current session history\n"
                    "• [cyan]session[/cyan] - Show current session ID\n\n"
                    "[bold]Or just type your question/command to interact with the agent.[/bold]",
                    title="Help",
                    border_style="green"
                ))
                continue
            
            if user_input.lower() == 'servers':
                console.print("\n[bold]Connected MCP Servers:[/bold]")
                for server in config.get_enabled_servers():
                    console.print(f"  • [cyan]{server.name}[/cyan]: {server.description}")
                continue
            
            if user_input.lower() == 'new':
                session_id = f"cli_session_{uuid.uuid4().hex[:8]}"
                console.print(f"[bold green]Started new session: {session_id}[/bold green]")
                continue
            
            if user_input.lower() == 'sessions':
                sessions = session_store.list_sessions()
                if not sessions:
                    console.print("[dim]No saved sessions found.[/dim]")
                else:
                    table = Table(title="Saved Sessions")
                    table.add_column("Session ID", style="cyan")
                    table.add_column("Title", style="white")
                    table.add_column("Messages", justify="right")
                    table.add_column("Updated", style="dim")
                    
                    for s in sessions[:10]:  # Show last 10
                        table.add_row(
                            s.session_id[:20] + "..." if len(s.session_id) > 20 else s.session_id,
                            (s.title[:30] + "...") if len(s.title) > 30 else s.title,
                            str(len(s.messages)),
                            s.updated_at[:19]
                        )
                    console.print(table)
                continue
            
            if user_input.lower().startswith('load '):
                load_session_id = user_input[5:].strip()
                session = session_store.get_session(load_session_id)
                if session is None:
                    console.print(f"[bold red]Session not found: {load_session_id}[/bold red]")
                else:
                    session_id = load_session_id
                    user_id = session.user_id
                    console.print(f"[bold green]Loaded session: {session_id}[/bold green]")
                    console.print(f"[dim]Title: {session.title}[/dim]")
                    console.print(f"[dim]Messages: {len(session.messages)}[/dim]")
                    
                    # Show recent messages
                    if session.messages:
                        console.print("\n[bold]Recent conversation:[/bold]")
                        for msg in session.messages[-4:]:  # Last 4 messages
                            role_color = "cyan" if msg.role == "user" else "magenta"
                            role_label = "You" if msg.role == "user" else "Agent"
                            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                            console.print(f"[{role_color}]{role_label}[/{role_color}]: {content_preview}")
                continue
            
            if user_input.lower() == 'history':
                session = session_store.get_session(session_id)
                if session is None or not session.messages:
                    console.print("[dim]No messages in current session.[/dim]")
                else:
                    console.print(f"\n[bold]Session History ({len(session.messages)} messages):[/bold]\n")
                    for i, msg in enumerate(session.messages):
                        role_color = "cyan" if msg.role == "user" else "magenta"
                        role_label = "You" if msg.role == "user" else "Agent"
                        console.print(f"[dim]{i+1}.[/dim] [{role_color}]{role_label}[/{role_color}]:")
                        console.print(Markdown(msg.content))
                        console.print()
                continue
            
            if user_input.lower() == 'session':
                console.print(f"[bold]Current Session ID:[/bold] {session_id}")
                session = session_store.get_session(session_id)
                if session:
                    console.print(f"[dim]Title: {session.title}[/dim]")
                    console.print(f"[dim]Messages: {len(session.messages)}[/dim]")
                continue
            
            # Send to agent
            console.print("\n[bold magenta]Agent[/bold magenta]: ", end="")
            try:
                response = await agent.chat(
                    user_input=user_input,
                    user_id=user_id,
                    session_id=session_id
                )
                # Render markdown response
                console.print(Markdown(response))
            except Exception as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
    
    finally:
        await agent.cleanup()


def run_server():
    """Run the FastAPI web server."""
    import uvicorn
    
    console.print(Panel.fit(
        f"[bold blue]Starting Orchestrator Agent Web API[/bold blue]\n"
        f"Host: {config.host}\n"
        f"Port: {config.port}\n"
        f"Model: {config.model_name}\n"
        f"Web UI: http://{config.host}:{config.port}/",
        title="Web Server",
        border_style="blue"
    ))
    
    uvicorn.run(
        "orchestrator.main:app",
        host=config.host,
        port=config.port,
        reload=False
    )


def main():
    """Main entry point - supports both CLI and server modes."""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "serve" or mode == "server" or mode == "api":
            run_server()
        elif mode == "cli" or mode == "chat":
            asyncio.run(run_cli())
        else:
            console.print(f"[bold red]Unknown mode: {mode}[/bold red]")
            console.print("Usage: orchestrator [cli|serve]")
            console.print("  cli   - Start interactive CLI chat")
            console.print("  serve - Start web API server")
            sys.exit(1)
    else:
        # Default to CLI mode
        asyncio.run(run_cli())


if __name__ == "__main__":
    main()