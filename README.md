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
`--dry-run` runs without CorelDRAW (records calls only). `pytest` runs the tests.

## Layout
- `coreldraw_agent/backend.py` – CorelDRAW COM backend + mock
- `coreldraw_agent/tools.py` – tool schemas and dispatcher
- `coreldraw_agent/agent.py` – tool-use loop
- `main.py` – CLI

To add a capability, add a method to the backends and a schema in `tools.py`.
