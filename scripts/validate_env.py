"""Valida o ambiente para rodar o agente: pré-requisitos + handshake MCP do Appium."""

import asyncio
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.appium_agent import build_mcp_tools

CHECKS = [
    ("Node.js (>=22)", shutil.which("node")),
    ("npm", shutil.which("npm")),
    ("npx", shutil.which("npx")),
    ("Java (JDK 8+)", shutil.which("java")),
    ("adb (Android SDK platform-tools)", shutil.which("adb")),
]


def check_prereqs() -> bool:
    ok = True
    print("== Pré-requisitos ==")
    for name, binary in CHECKS:
        found = binary is not None
        status = "OK" if found else "FALTANDO"
        print(f"  [{status}] {name}: {binary or '(não encontrado no PATH)'}")
        if name.startswith("adb") and not found:
            print(
                "        → Instale o Android SDK (platform-tools) e ajuste ANDROID_HOME."
            )
        ok = ok and found

    android_home = None
    import os

    android_home = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    print(f"  [{'OK' if android_home else 'FALTANDO'}] ANDROID_HOME: {android_home or '(não definida)'}")
    return ok and bool(android_home)


async def check_mcp_handshake() -> int:
    print("\n== Handshake MCP (appium-mcp) ==")
    tools = build_mcp_tools()
    try:
        await tools.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERRO] Falha ao iniciar MCPTools: {exc}")
        return 1

    funcs = tools.get_async_functions()
    print(f"  [OK] Servidor conectado — {len(funcs)} tools disponíveis")
    for name in sorted(funcs):
        print(f"       - {name}")
    await tools.close()
    return 0


def main() -> int:
    prereqs_ok = check_prereqs()
    if not prereqs_ok:
        print("\nAlguns pré-requisitos faltando — consulte PLAN.md. Seguindo mesmo assim com o handshake...")
    return asyncio.run(check_mcp_handshake())


if __name__ == "__main__":
    raise SystemExit(main())