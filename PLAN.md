# Plano — Agente mobile QA com Appium + Agno

## Veredito

- **Possível?** Sim. Agno (Python) + servidor MCP oficial da Appium.
- **Lib:** Agno — fork leve, integração MCP de primeira classe (`agno.tools.mcp.MCPTools`).
- **Linguagem:** Python. Agno é Python-only; o MCP server Appium é agnóstico de linguagem (disparado via `npx`). JS não tem equivalente real ao agno.

## Arquitetura

```
Usuário (intenção em linguagem natural)
   ↓
Agno Agent (Python, modelo OpenRouter)  ← "cérebro"
   ↓  MCPTools (stdio, npx appium-mcp@latest)
Appium MCP server                       ← "executor" (sessões, UiAutomator2)
   ↓
Android device/emulador
```

O MCP server expõe: `select_device`, `appium_session_management` (create/delete), `appium_find_element` (find por visão/AI opcional), `appium_gesture` (tap, swipe, type), `appium_screenshot`, `appium_get_page_source`, gravação de tela e geração de testes.

## Pré-requisitos do ambiente

- Node.js 22+, JDK 8+, Android SDK (`ANDROID_HOME`), `adb`, emulador/dispositivo Android
- Opcional: `AI_VISION_ENABLED` + provider de modelo de visão (OpenAI-compatible) para find por IA

## Passos de implementação

1. Estrutura de projeto Python (`pyproject.toml`, venv via `uv`)
2. Instalar `agno`, `mcp`, `openai`
3. `config/capabilities.json` com capabilities do app Android (`appium:automationName=UiAutomator2`)
4. `appium_agent.py`: `Agent(model=OpenRouter(...), tools=[MCPTools(...)], instructions=...)`
   - `MCPTools` conecta via `StdioServerParameters(command="npx", args=["-y", "appium-mcp@latest"], env={...})`
   - Ciclo de vida async: `connect()` → rodar → `close()`
5. Modo orquestrador generalista: gerar/planejar testes, executar via MCP tools com `show_tool_calls=True`, coletar screenshots/page source como evidência, emitir relatório final (pass/fail, causa)
6. CLI de entrada: `python main.py "testar login com credenciais de teste e verificar dashboard"`
7. `.env` para `OPENROUTER_API_KEY` (+ chaves de visão); `NO_UI=true` para reduzir tokens

## Roteiro de validação

1. `adb devices` — device/emulador listado
2. Subir emulador e conferir reconhecimento
3. `npx appium-mcp@latest` — smoke test do handshake MCP
4. Rodar um teste de exemplo contra o app

## Melhorias adotadas (fonte: Software Testing Trends — Appium MCP Server)

- Capabilities Android ampliadas (`newCommandTimeout`, `connectHardwareKeyboard`, `ensureWebviewsHavePages`, `nativeWebScreenshot`, `appPackage`/`appActivity`)
- Modos de operação no CLI: `test`, `explore` (mapeia o app), `debug` (causa raiz + correção), `generate` (gera testes) e `smoke` (offline)
- Instrução de sessão alinhada ao servidor oficial: sempre `select_device` com `platform="android"` antes de criar sessão

## Riscos / decisões anotadas

- Latência: cada ação custa 2-4s (raciocínio LLM) → adequado para E2E funcional, não benchmark
- Custo = LLM por tool call; `NO_UI=true` reduz 60-90% dos tokens
- Segurança: MCP server é single-user local — não expor como serviço compartilhado
- Pin `mcp>=1.2,<2.0`: agno 2.8.x usa `McpError` removido em mcp 2.0
- `show_tool_calls` não existe no agno 2.8 (removido); tool calls aparecem no streaming