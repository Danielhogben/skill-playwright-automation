#!/usr/bin/env python3
"""playwright-automation — Cross-browser web automation with Playwright."""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[0m"
BOLD = "\033[1m"

SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config.json"
SCREENSHOTS_DIR = SKILL_DIR / "screenshots"
PDFS_DIR = SKILL_DIR / "pdfs"
TRACES_DIR = SKILL_DIR / "traces"
SCRIPTS_DIR = SKILL_DIR / "scripts"
RESULTS_DIR = SKILL_DIR / "results"


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def check_playwright():
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        print(f"{R}Playwright not installed.{W}")
        print(f"  Install: {C}pip install playwright && playwright install{W}")
        return False


async def cmd_init(args):
    print(f"{C}Installing Playwright browsers...{W}")

    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "playwright", "install",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode()
    print(output)

    if proc.returncode == 0:
        print(f"\n{G}Playwright browsers installed successfully.{W}")
    else:
        print(f"\n{R}Browser installation had issues. Try manually: playwright install{W}")

    # Create project structure
    for d in [SCREENSHOTS_DIR, PDFS_DIR, TRACES_DIR, SCRIPTS_DIR, RESULTS_DIR]:
        d.mkdir(exist_ok=True)

    cfg = load_config()
    cfg["initialized"] = True
    cfg["init_date"] = datetime.now().isoformat()
    save_config(cfg)

    print(f"{Y}Project directories created:{W}")
    for d in [SCREENSHOTS_DIR, PDFS_DIR, TRACES_DIR, SCRIPTS_DIR]:
        print(f"  {d}")


async def cmd_screenshot(args):
    if not check_playwright():
        sys.exit(1)

    from playwright.async_api import async_playwright

    url = args.url
    browser_type = args.browser
    print(f"{C}Capturing:{W} {url} ({browser_type})")

    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    filename = args.output or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    out_path = SCREENSHOTS_DIR / filename

    async with async_playwright() as p:
        browser_launcher = getattr(p, browser_type)
        browser = await browser_launcher.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=2 if args.retina else 1,
        )
        page = await ctx.new_page()

        try:
            await page.goto(url, wait_until=args.wait_until, timeout=30000)
        except Exception as e:
            print(f"{Y}Navigation warning:{W} {e}")

        await page.screenshot(path=str(out_path), full_page=args.full_page)
        await browser.close()

    size_kb = out_path.stat().st_size / 1024
    print(f"{G}Screenshot saved:{W} {out_path}")
    print(f"{Y}Size:{W} {size_kb:.1f} KB")


async def cmd_pdf(args):
    if not check_playwright():
        sys.exit(1)

    from playwright.async_api import async_playwright

    url = args.url
    print(f"{C}Generating PDF:{W} {url}")

    PDFS_DIR.mkdir(exist_ok=True)
    filename = args.output or f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = PDFS_DIR / filename

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)

        pdf_options = {
            "path": str(out_path),
            "format": args.format,
            "print_background": args.background,
        }
        if args.landscape:
            pdf_options["landscape"] = True

        await page.pdf(**pdf_options)
        await browser.close()

    size_kb = out_path.stat().st_size / 1024
    print(f"{G}PDF saved:{W} {out_path}")
    print(f"{Y}Size:{W} {size_kb:.1f} KB")


async def cmd_trace(args):
    if not check_playwright():
        sys.exit(1)

    from playwright.async_api import async_playwright

    url = args.url
    print(f"{C}Recording trace:{W} {url}")

    TRACES_DIR.mkdir(exist_ok=True)
    filename = args.output or f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    out_path = TRACES_DIR / filename

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        await ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            # Perform some interactions for trace data
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"{Y}Page warning:{W} {e}")

        await ctx.tracing.stop(path=str(out_path))
        await browser.close()

    size_kb = out_path.stat().st_size / 1024
    print(f"{G}Trace saved:{W} {out_path}")
    print(f"{Y}Size:{W} {size_kb:.1f} KB")
    print(f"{Y}View:{W} npx playwright show-trace {out_path}")


async def cmd_test(args):
    if not check_playwright():
        sys.exit(1)

    script = Path(args.script)
    if not script.exists():
        print(f"{R}Script not found:{W} {script}")
        sys.exit(1)

    print(f"{C}Running test:{W} {script}")

    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode()
    print(output)

    if proc.returncode == 0:
        print(f"\n{G}Test passed.{W}")
    else:
        print(f"\n{R}Test failed (exit code {proc.returncode}).{W}")

    RESULTS_DIR.mkdir(exist_ok=True)
    result = {
        "script": str(script),
        "exit_code": proc.returncode,
        "output": output,
        "timestamp": datetime.now().isoformat(),
    }
    out = RESULTS_DIR / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(result, indent=2))


async def cmd_record(args):
    if not check_playwright():
        sys.exit(1)

    task = args.task
    print(f"{C}Generating test script for:{W} {task}")

    # Generate a Playwright script from natural language
    steps = task.lower()

    script_lines = [
        "#!/usr/bin/env python3",
        '"""Auto-generated Playwright test script."""',
        "",
        "import asyncio",
        "from playwright.async_api import async_playwright",
        "",
        "",
        "async def main():",
        "    async with async_playwright() as p:",
        "        browser = await p.chromium.launch(headless=False)",
        "        page = await browser.new_page()",
        "",
    ]

    # Parse common actions from task description
    if "navigate" in steps or "go to" in steps or "open" in steps:
        for word in ["http://", "https://"]:
            if word in task:
                url_start = task.index(word)
                url_end = task.find(" ", url_start)
                url = task[url_start:] if url_end == -1 else task[url_start:url_end]
                script_lines.append(f'        await page.goto("{url}")')
                break

    if "screenshot" in steps:
        script_lines.append('        await page.screenshot(path="recorded_screenshot.png")')

    if "click" in steps:
        script_lines.append('        # Click element (update selector)')
        script_lines.append('        # await page.click("selector")')

    if "type" in steps or "fill" in steps or "enter" in steps:
        script_lines.append('        # Fill form field (update selector and value)')
        script_lines.append('        # await page.fill("selector", "value")')

    script_lines.extend([
        "",
        "        await browser.close()",
        "",
        "",
        'if __name__ == "__main__":',
        "    asyncio.run(main())",
    ])

    SCRIPTS_DIR.mkdir(exist_ok=True)
    filename = args.output or f"recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    out_path = SCRIPTS_DIR / filename
    out_path.write_text("\n".join(script_lines))
    out_path.chmod(0o755)

    print(f"{G}Script generated:{W} {out_path}")
    print(f"\n{Y}Content:{W}")
    print("\n".join(script_lines))


async def cmd_codegen(args):
    if not check_playwright():
        sys.exit(1)

    url = args.url or ""
    print(f"{C}Launching Playwright Codegen...{W}")
    if url:
        print(f"{C}URL:{W} {url}")
    print(f"{Y}A browser window will open. Interact with the page to generate test code.{W}\n")

    SCRIPTS_DIR.mkdir(exist_ok=True)
    output = SCRIPTS_DIR / f"codegen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    cmd = [sys.executable, "-m", "playwright", "codegen", f"--output={output}"]
    if url:
        cmd.append(url)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()

    if output.exists():
        print(f"\n{G}Generated script saved:{W} {output}")
        content = output.read_text()
        if content:
            print(f"\n{Y}Preview:{W}")
            print(content[:500])
    else:
        print(f"\n{Y}Codegen closed without generating output.{W}")


async def main():
    parser = argparse.ArgumentParser(
        description="Cross-browser automation with Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # init
    sub.add_parser("init", help="Install browsers and set up project")

    # screenshot
    p = sub.add_parser("screenshot", help="Capture a screenshot")
    p.add_argument("url", help="URL to capture")
    p.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    p.add_argument("--output", "-o", help="Output filename")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--full-page", action="store_true")
    p.add_argument("--retina", action="store_true")
    p.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])

    # pdf
    p = sub.add_parser("pdf", help="Generate a PDF from a web page")
    p.add_argument("url", help="URL to convert")
    p.add_argument("--output", "-o", help="Output filename")
    p.add_argument("--format", default="A4", help="Page format")
    p.add_argument("--landscape", action="store_true")
    p.add_argument("--background", action="store_true", default=True)

    # trace
    p = sub.add_parser("trace", help="Generate a trace file for debugging")
    p.add_argument("url", help="URL to trace")
    p.add_argument("--output", "-o", help="Output filename")

    # test
    p = sub.add_parser("test", help="Run a Playwright test script")
    p.add_argument("script", help="Path to test script")

    # record
    p = sub.add_parser("record", help="Generate a test script from description")
    p.add_argument("task", help="Task description")
    p.add_argument("--output", "-o", help="Output script filename")

    # codegen
    p = sub.add_parser("codegen", help="Launch Playwright Codegen")
    p.add_argument("url", nargs="?", default="", help="URL to open")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "init": cmd_init,
        "screenshot": cmd_screenshot,
        "pdf": cmd_pdf,
        "trace": cmd_trace,
        "test": cmd_test,
        "record": cmd_record,
        "codegen": cmd_codegen,
    }
    await cmds[args.command](args)


if __name__ == "__main__":
    asyncio.run(main())
