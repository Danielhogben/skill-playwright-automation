# playwright-automation — Cross-Browser Automation

Multi-browser web automation and testing with [Playwright](https://playwright.dev/python/). Supports Chromium, Firefox, and WebKit with a single API.

## Capabilities

- **init** — Install browsers and set up a Playwright project
- **record** — Record browser actions into a reusable test script
- **test** — Run Playwright test scripts
- **screenshot** — Capture screenshots of URLs
- **pdf** — Generate PDFs from web pages
- **trace** — Generate trace files for step-by-step debugging
- **codegen** — Launch Playwright Codegen for interactive test authoring

## Setup

```bash
pip install playwright
playwright install
```

## Usage

```bash
# Initialize and install browsers
python3 playwright_automation.py init

# Capture a screenshot
python3 playwright_automation.py screenshot https://example.com --browser chromium

# Generate a PDF
python3 playwright_automation.py pdf https://example.com -o output.pdf

# Record actions into a test script
python3 playwright_automation.py record "Navigate to example.com, click the link" -o test.py

# Run a test script
python3 playwright_automation.py test test_script.py

# Generate a trace for debugging
python3 playwright_automation.py trace https://example.com

# Launch codegen (opens a browser window for interactive test writing)
python3 playwright_automation.py codegen https://example.com
```

## Supported Browsers

- Chromium (default)
- Firefox
- WebKit (Safari-like)

## Output

- Screenshots saved to `screenshots/`
- PDFs saved to `pdfs/`
- Traces saved to `traces/`
- Generated scripts saved to `scripts/`
