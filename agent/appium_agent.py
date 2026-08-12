import asyncio
import os
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def default_capabilities_config() -> Path:
    return PROJECT_ROOT / "config" / "capabilities.json"


def build_mcp_tools() -> MCPTools:
    """Constrói MCPTools apontando para o servidor MCP oficial do Appium."""
    env: dict[str, str] = {
        "ANDROID_HOME": os.getenv("ANDROID_HOME", ""),
        "CAPABILITIES_CONFIG": os.getenv(
            "CAPABILITIES_CONFIG", str(default_capabilities_config())
        ),
        "SCREENSHOTS_DIR": os.getenv(
            "SCREENSHOTS_DIR", str(PROJECT_ROOT / "screenshots")
        ),
        "NO_UI": os.getenv("NO_UI", "true"),
        "APPIUM_MCP_APPS_ENABLED": os.getenv("APPIUM_MCP_APPS_ENABLED", "false"),
    }

    for var in ("AI_VISION_ENABLED", "AI_VISION_API_BASE_URL", "AI_VISION_API_KEY"):
        value = os.getenv(var)
        if value:
            env[var] = value

    env = {k: v for k, v in env.items() if v}

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "appium-mcp@latest"],
        env=env,
    )
    return MCPTools(server_params=server_params, name="appium-mcp")


def default_model_id() -> str:
    return os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def build_agent(model_id: str | None = None) -> Agent:
    """Monta o agente orquestrador mobile QA."""
    return Agent(
        model=OpenRouter(id=model_id or default_model_id()),
        tools=[build_mcp_tools()],
        name="Appium QA Agent",
        markdown=True,
        instructions=dedent(
            """\
            You are a mobile QA agent that orchestrates end-to-end tests on Android apps
            through the Appium MCP server. You write test plans, execute them on a real
            device/emulator, gather evidence, and report results.

            ## Workflow
            1. PLAN: from the user's intent, break the test into concrete steps
               (screen, action, expected result).
            2. SETUP: call appium_session_management (action=create) to start a session;
               if not sure about the device, call select_device first.
            3. EXECUTE: for each step use the MCP tools:
               - appium_find_element (prefer accessibility_id/resource id over xpath)
               - appium_gesture (tap, type_text, swipe, etc.)
               - appium_get_page_source / appium_screenshot to inspect state
            4. VERIFY: confirm expected results on each screen; if an action fails or an
               element is missing, capture a screenshot as evidence before changing state.
            5. REPORT: summarize PASS/FAIL per step with cause and evidence (screenshot
               paths), and finish with a final verdict.

            ## Rules
            - Always confirm a session exists before calling device tools. Create one if needed.
            - After clicking/tapping, re-fetch page source or take a screenshot before asserting.
            - Keep test evidence: save screenshots (SCREENSHOTS_DIR) and reference their paths.
            - Never invent elements: base actions only on what you observe in page source.
            - Run the test as the user asked; do not skip steps silently.
            - End with a clear overall verdict (PASSED / FAILED) and any follow-up needed.
            """
        ),
    )