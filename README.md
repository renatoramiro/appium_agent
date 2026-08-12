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
# valida o sistema sem device/chave: audita pré-requisitos + handshake MCP
uv run python main.py --mode smoke

# valida ambiente + handshake MCP (igual ao smoke, sai sem listar tools)
uv run python scripts/validate_env.py
```

### Modos de operação

| Modo | Descrição | Exemplo |
| --- | --- | --- |
| `test` | Executa um teste E2E orquestrado pela intenção | `uv run python main.py "testar login com credenciais de teste e verificar dashboard"` |
| `explore` | Varre o app, mapeia telas/elementos/fluxos e gera doc markdown | `uv run python main.py --mode explore` |
| `debug` | Diagnostica falha: reproduz, coleta screenshot/page source, dá causa raiz + correção | `uv run python main.py --mode debug "elemento não encontrado após login"` |
| `generate` | Gera código de teste (Java/TestNG via `appium_generate_tests`) a partir de texto | `uv run python main.py --mode generate "fluxo de login com credenciais inválidas"` |
| `smoke` | Offline (sem device/LLM): valida plating agno → MCP → appium-mcp e audita pré-requisitos | `uv run python main.py --mode smoke` |

```bash
# salva o relatório em arquivo
uv run python main.py "testar fluxo de busca" -o reports/busca.md
# streaming desligado
uv run python main.py --mode explore --no-stream

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
- O agente chama `select_device` com `platform="android"` antes de criar sessão (exigência do servidor oficial).
- Veja `PLAN.md` para o plano completo e riscos.

## Testabilidade (o que dá para rodar agora)

- **Agora**: `--mode smoke` e `scripts/validate_env.py` validam todo o plumbing (agno → MCP → appium-mcp), sem precisar de device ou API key.
- **Teste E2E real** exige, no host: `adb` + `ANDROID_HOME`, um APK em `config/capabilities.json`, um emulador/dispositivo ligado e `OPENROUTER_API_KEY`. O smoke audita esses 4 itens.