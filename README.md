# CorelDRAW Agent

Autonomous agent that draws in CorelDRAW from a text prompt. A Claude model
plans the drawing and calls tools (`new_document`, `rectangle`, `ellipse`,
`line`, `polygon`, `text`, `save`, `export`) which are executed against
CorelDRAW through COM automation.

## Setup (Windows, CorelDRAW installed)
```
pip install -r requirements.txt
set ANTHROPIC_API_KEY=...
python main.py "A5 poster: red sun over blue mountains, title 'Summer'"
```
Or just double-click `run.bat` (sets up venv, asks for key and prompt; `run.bat "prompt" --dry-run` also works).

`--dry-run` runs without CorelDRAW (records calls only). `pytest` runs the tests.

## Layout
- `coreldraw_agent/backend.py` – CorelDRAW COM backend + mock
- `coreldraw_agent/tools.py` – tool schemas and dispatcher
- `coreldraw_agent/agent.py` – tool-use loop
- `main.py` – CLI

To add a capability, add a method to the backends and a schema in `tools.py`.

## Desktop app (.exe)
`gui.py` is a small window (API key, prompt, live log). To get `CorelAgent.exe`:
- **GitHub (automatic):** every push runs `.github/workflows/build.yml` on Windows, runs tests and
  uploads `CorelAgent.exe` (Actions -> run -> Artifacts). Pushes to `main` also update the
  **latest** release; tags `v*` create a versioned release.
- **Locally:** run `build_exe.bat` -> `dist\CorelAgent.exe`.

## Test machine
Windows 10/11 with CorelDRAW installed (2018+), internet access, an Anthropic API key.
Start CorelDRAW once first so any licence/welcome dialogs are dismissed.
