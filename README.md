# Appium QA Agent

Agente de QA mobile que testa apps **Android** via Appium usando a lib **agno** (Python + OpenRouter).

## Arquitetura

```
Intenção em linguagem natural
   ↓
Agno Agent (OpenRouter)          ← "cérebro" (planeja, executa, reporta)
   ↓  MCPTools (stdio)
appium-mcp (npx appium-mcp@latest)  ← "executor" (sessões UiAutomator2)
   ↓
Dispositivo/emulador Android
```

## Setup

```bash
uv sync --extra dotenv
cp .env.example .env   # preencha OPENROUTER_API_KEY, ANDROID_HOME
# configure config/capabilities.json (caminho do APK, udid, platformVersion)
```

Pré-requisitos do host: Node.js 22+, JDK 8+, Android SDK + `adb`, emulador/dispositivo.

## Uso

```bash
# valida ambiente + handshake MCP
uv run python scripts/validate_env.py

# executa um teste por intenção em linguagem natural
uv run python main.py "testar login com credenciais de teste e verificar dashboard"

# salva o relatório em arquivo
uv run python main.py "testar fluxo de busca" -o reports/busca.md
```

## Variáveis de ambiente

| Variável | Descrição |
| --- | --- |
| `OPENROUTER_API_KEY` | Chave da API do OpenRouter (obrigatória) |
| `OPENROUTER_MODEL` | Modelo OpenRouter (default `openai/gpt-4o-mini`) |
| `ANDROID_HOME` | Caminho do Android SDK |
| `CAPABILITIES_CONFIG` | Caminho do `capabilities.json` (default `config/capabilities.json`) |
| `NO_UI` | `true` reduz tokens/UI do MCP (default `true`) |
| `SCREENSHOTS_DIR` | Pasta de evidências (default `./screenshots`) |
| `AI_VISION_ENABLED` | Habilita find de elemento por visão (requer base URL + key) |
| `AI_VISION_API_BASE_URL` / `AI_VISION_API_KEY` | Provider de visão OpenAI-compatible |

## Notas

- Each action gera latência de ~2-4s (raciocínio LLM) — ideal para E2E funcional, não para benchmark.
- O MCP server é single-user/local — não exponha como serviço compartilhado.
- Veja `PLAN.md` para o plano completo e riscos.