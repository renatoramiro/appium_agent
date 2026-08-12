import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from agent.appium_agent import (
    MODE_DEFAULT_PROMPTS,
    build_agent,
    build_mcp_tools,
    default_capabilities_config,
)

ROOT = Path(__file__).resolve().parent
MODES = list(MODE_DEFAULT_PROMPTS) + ["smoke"]


async def run_agent(
    prompt: str, model_id: str | None, mode: str, stream: bool, output: Path | None
) -> None:
    mcp_tools = build_mcp_tools()
    agent = None
    try:
        await mcp_tools.connect()
        agent = build_agent(model_id=model_id, mode=mode)
        if stream:
            await agent.aprint_response(prompt, stream=True)
        else:
            response = await agent.arun(prompt)
            print(response.content)
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(str(response.content), encoding="utf-8")
    finally:
        if agent is not None:
            reset = getattr(agent, "arun_reset", None)
            if callable(reset):
                await reset()
        await mcp_tools.close()


def load_capabilities() -> dict:
    path = default_capabilities_config()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def check_android_ready(quiet: bool = False) -> bool:
    """Audita os pré-requisitos Android e retorna se um teste E2E é possível."""
    import shutil

    checks = {
        "adb no PATH": shutil.which("adb") is not None,
        "ANDROID_HOME definida": bool(
            os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
        ),
    }
    caps = load_capabilities().get("android", {})
    app = caps.get("appium:app", "")
    checks["APK configurado em capabilities.json"] = bool(app) and Path(app).exists()
    checks["OPENROUTER_API_KEY definida"] = bool(os.getenv("OPENROUTER_API_KEY"))

    for name, ok in checks.items():
        if not quiet:
            print(f"  [{'OK' if ok else 'FALTANDO'}] {name}")
    return all(checks.values())


async def run_smoke() -> None:
    """Modo smoke: valida o sistema sem precisar de device/chave/LLM."""
    print("== Pré-requisitos Android ==")
    ready = check_android_ready()
    if not ready:
        print("\n  → E2E real exige: adb + ANDROID_HOME + APK + OPENROUTER_API_KEY.")
        print("    Ainda assim, o plumbing abaixo valida o sistema (agno → MCP → appium-mcp):")

    print("\n== Handshake MCP (appium-mcp) ==")
    tools = build_mcp_tools()
    try:
        await tools.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERRO] Falha ao iniciar MCPTools: {exc}")
        return

    funcs = tools.get_async_functions()
    print(f"  [OK] Servidor conectado — {len(funcs)} tools disponíveis")

    fn = funcs.get("select_device")
    if fn is not None:
        print("  [i] Sondando select_device (esperado: erro de ADB/sessão sem device)...")
        try:
            result = await fn.entrypoint(platform="android")
            print(f"  [OK] Tool executada — resposta: {str(result)[:300]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [ERRO] Falha ao executar select_device: {exc}")
    await tools.close()
    print("\nPlumbing OK. Para E2E real, cubra os pré-requisitos marcados como FALTANDO.")


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(
        description="Agente mobile QA: testa apps Android via Appium (MCP) com agno."
    )
    parser.add_argument("prompt", nargs="?", help="Intenção de teste em linguagem natural")
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="test",
        help=f"Modo de operação: {', '.join(MODES)}. smoke = valida o sistema offline.",
    )
    parser.add_argument("--model", default=None, help="ID do modelo no OpenRouter")
    parser.add_argument("--no-stream", action="store_true", help="Não usar streaming na resposta")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Caminho do arquivo para salvar o relatório final",
    )
    args = parser.parse_args()

    if args.mode == "smoke":
        asyncio.run(run_smoke())
        return

    if not os.getenv("OPENROUTER_API_KEY"):
        print("AVISO: OPENROUTER_API_KEY não definida no ambiente nem em .env")
    if not os.getenv("ANDROID_HOME"):
        print("AVISO: ANDROID_HOME não definida — verifique o roteiro de validação (PLAN.md).")

    prompt = args.prompt or MODE_DEFAULT_PROMPTS.get(args.mode, MODE_DEFAULT_PROMPTS["test"])
    asyncio.run(
        run_agent(prompt, args.model, args.mode, stream=not args.no_stream, output=args.output)
    )


if __name__ == "__main__":
    main()