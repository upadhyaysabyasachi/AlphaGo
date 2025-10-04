## LinkedIn Post Style Refiner

Try it out here:
```
https://jayc24-autolinkedin.hf.space/
```
Run locally:

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python app.py
```

Notes:
- Paste your draft, adjust optional style rules, click "Refine in My Style".
- Two variations are always produced; enable the checkbox to get a third.
- All processing is local; nothing is stored or sent externally.

### 2: Review & Publish (Simulated)

- Switch to the "Publish" tab to edit the final draft.
- Optional: attach images/videos via the file picker.
- Choose mode "Now" or "Schedule Later" (provide ISO time like `2025-01-31T14:30:00Z`).
- Leave "Dry Run" checked to simulate posting; result shows a preview URL.
- Scheduled simulations will be logged and executed in the background.
- Logs are written to `published_log.jsonl` in the project directory.


### LLM mode via OpenRouter

- Set environment variables (copy `ENV_SAMPLE.txt` to `.env` or export):
  - `OPENROUTER_API_KEY`: your OpenRouter API key
  - `OPENROUTER_MODEL`: defaults to `openai/gpt-oss-20b:free`
  - `OPENROUTER_REFERER`: your app URL (can be http://localhost)
  - `OPENROUTER_APP_NAME`: e.g., "LinkedIn Refiner"
- In the Refine tab, use "Refine with LLM" to generate a version that respects Tone/Structure/Closing/Length.

### 3: Engagement

- Switch to the "Engagement" tab.
- Choose number of posts to analyze (uses local `published_log.jsonl`).
- Click "Fetch Stats" to see a table and chart (likes/comments/shares are simulated but deterministic).
- Click "Export CSV & PDF" to save a report under `exports/`.
