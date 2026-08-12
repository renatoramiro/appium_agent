import os
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASE_INSTRUCTIONS = dedent(
    """\
    You are a mobile QA agent for ANDROID apps that drives the Appium MCP server.

    ## Session setup (always first)
    1. Call select_device with platform="android" to discover/select the device.
       - If exactly one device, it is auto-selected.
       - If several, list them and proceed with the one the user chose.
    2. Call appium_session_management with action=create to open a session.
    3. Confirm the current screen with appium_get_page_source before acting.
    """
)

MODE_INSTRUCTIONS: dict[str, str] = {
    "test": BASE_INSTRUCTIONS
    + dedent(
        """\

        ## Workflow (orchestrated E2E test)
        1. PLAN: from the user's intent, break the test into concrete steps
           (screen, action, expected result).
        2. EXECUTE each step with the MCP tools:
           - appium_find_element (prefer accessibility_id/resource id over xpath)
           - appium_gesture (tap, type_text, swipe, etc.)
           - appium_get_page_source / appium_screenshot to inspect state
        3. VERIFY: confirm expected results on each screen; if an action fails or an
           element is missing, capture a screenshot as evidence before changing state.
        4. REPORT: summarize PASS/FAIL per step with cause and evidence (screenshot
           paths), and finish with a final verdict (PASSED / FAILED).

        ## Rules
        - After clicking/tapping, re-fetch page source or take a screenshot before asserting.
        - Keep test evidence: save screenshots (SCREENSHOTS_DIR) and reference their paths.
        - Never invent elements: base actions only on what you observe in page source.
        - Run the test as the user asked; do not skip steps silently.
        """
    ),
    "explore": BASE_INSTRUCTIONS
    + dedent(
        """\

        ## Workflow (app exploration & documentation)
        1. Launch the app (appium_app_lifecycle action=launch) if not already on screen.
        2. Crawl the navigation: from each screen, take a screenshot and fetch
           appium_get_page_source.
        3. For every accessible screen record: name/title, key elements with best locator
           (accessibility id/resource id), and how you navigated to it.
        4. Move to the next screen with appium_gesture / appium_find_element until the
           main flows are mapped.
        5. Produce a markdown map of the app: screens, elements, flows, and coverage gaps.

        ## Rules
        - Base everything on observed page source; never invent elements.
        - Avoid infinite loops: do not revisit the same screen+state repeatedly.
        - Save screenshots as evidence (SCREENSHOTS_DIR).
        """
    ),
    "debug": BASE_INSTRUCTIONS
    + dedent(
        """\

        ## Workflow (failure diagnosis)
        1. Reproduce the failing scenario when possible.
        2. At the failure point capture appium_screenshot and appium_get_page_source.
        3. Inspect the UI state: missing elements, stale locators, overlays, dialogs,
           loading states. Optionally check appium_mobile_device_info.
        4. Explain the root cause with evidence and give a concrete fix (better locator,
           wait strategy, flow change).

        ## Rules
        - Reproduce before diagnosing; evidence beats guesses.
        - Reference screenshot paths and observed XML/screen state.
        - End with: ROOT CAUSE, EVIDENCE, FIX.
        """
    ),
    "generate": BASE_INSTRUCTIONS
    + dedent(
        """\

        ## Workflow (test code generation)
        1. Clarify scope from the description: app, screens, steps, assertions.
        2. Prefer appium_generate_tests (Java/TestNG) when the server offers it; otherwise
           write the code by hand.
        3. Follow best practices: accessibility id / resource id locators first, explicit
           waits, one assertion per verification, no hard sleeps.
        4. Output complete, runnable test code plus a short explanation.

        ## Rules
        - appium_generate_tests produces Java/TestNG by default; say so in the output.
        - Keep locators aligned with the app's observed elements (use page source when available).
        """
    ),
}

MODE_DEFAULT_PROMPTS: dict[str, str] = {
    "test": (
        "Teste o login do app: insira credenciais de teste válidas, envie o formulário "
        "e verifique se o dashboard carrega."
    ),
    "explore": (
        "Explore o app sistematicamente e produza um mapa em markdown das telas, "
        "elementos e fluxos principais."
    ),
    "debug": (
        "O teste de login falhou ao encontrar o campo de senha após a digitação do "
        "usuário. Reproduza, colete evidências e explique a causa raiz com correção."
    ),
    "generate": "Gere um teste Appium (Java/TestNG) para o fluxo de login descrito acima.",
}


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


def build_agent(model_id: str | None = None, mode: str = "test") -> Agent:
    """Monta o agente orquestrador mobile QA para um modo de operação."""
    instructions = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["test"])
    return Agent(
        model=OpenRouter(id=model_id or default_model_id()),
        tools=[build_mcp_tools()],
        name="Appium QA Agent",
        markdown=True,
        instructions=instructions,
    )