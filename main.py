import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agent.appium_agent import build_agent, build_mcp_tools

ROOT = Path(__file__).resolve().parent


async def run(prompt: str, model_id: str | None, stream: bool, output: Path | None) -> None:
    mcp_tools = build_mcp_tools()
    agent = None
    try:
        await mcp_tools.connect()
        agent = build_agent(model_id=model_id)
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


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(
        description="Agente mobile QA: testa apps Android via Appium (MCP) com agno."
    )
    parser.add_argument("prompt", nargs="?", help="Intenção de teste em linguagem natural")
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

    prompt = args.prompt or (
        "Teste o login do app: insira credenciais de teste válidas, "
        "envie o formulário e verifique se o dashboard carrega."
    )

    if not os.getenv("OPENROUTER_API_KEY"):
        print("AVISO: OPENROUTER_API_KEY não definida no ambiente nem em .env")
    if not os.getenv("ANDROID_HOME"):
        print("AVISO: ANDROID_HOME não definida — verifique o roteiro de validação (PLAN.md).")

    asyncio.run(run(prompt, args.model, stream=not args.no_stream, output=args.output))


if __name__ == "__main__":
    main()