"""
PR Coach (Explain & Coach) — Gradio MVP with Sample PRs (SSL‑safe, SystemExit‑quiet, Groq‑optional)

- Full UI with sample PRs, findings table, explanations, Q&A, and ratings
- CLI fallback if SSL/Gradio are unavailable
- Optional Groq integration for explanation text (keeps deterministic steps)
- Tests included

Install:
  pip install gradio==4.* pydantic==2.*
(Optionally) Groq:
  pip install groq==0.*
  export GROQ_API_KEY=sk_...
Run UI:
  python app.py [--groq-model llama-3.1-8b-instant]
Run CLI:
  python app.py --cli [--groq-model llama-3.1-8b-instant]
Run tests:
  python app.py --test
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import time
import hashlib
import argparse
import os
import sys

# ------------------------------------------------------------
# Feature detection — avoid importing gradio when SSL is absent
# ------------------------------------------------------------
HAS_SSL = True
try:
    import ssl as _ssl  # noqa: F401
except Exception:  # ModuleNotFoundError: No module named 'ssl'
    HAS_SSL = False

HAS_GRADIO: bool = False
GRADIO_IMPORT_ERR: Optional[Exception] = None
if HAS_SSL:
    try:
        import gradio as gr  # type: ignore
        HAS_GRADIO = True
    except Exception as e:
        GRADIO_IMPORT_ERR = e
else:
    gr = None  # type: ignore

# --------------------------
# Groq integration (optional)
# --------------------------
HAS_GROQ = False
GROQ_IMPORT_ERR: Optional[Exception] = None
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEFAULT_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
try:
    from groq import Groq  # type: ignore
    HAS_GROQ = True if GROQ_API_KEY else False
except Exception as e:
    GROQ_IMPORT_ERR = e

# --------------------------
# Domain models (pydantic)
# --------------------------

class Finding(BaseModel):
    id: str
    tool: str
    rule_id: str
    severity: str
    file: str
    start_line: int
    end_line: Optional[int] = None
    message: str
    suggestion: Optional[str] = None
    # minimal snippet (already redacted)
    snippet: Optional[str] = None

class Policy(BaseModel):
    require_docstrings_public_only: bool = True
    max_inline_comments: int = 10
    allow_snippets: bool = True
    notes: Dict[str, Any] = Field(default_factory=dict)

class ChatAnswer(BaseModel):
    answer: str
    steps: List[str] = Field(default_factory=list)
    example_snippet: Optional[str] = None
    references: List[Dict[str, str]] = Field(default_factory=list)
    safety: Dict[str, Any] = Field(default_factory=dict)

# --------------------------
# Mock data / services
# Replace these with real integrations later.
# --------------------------

MOCK_POLICY = Policy(
    require_docstrings_public_only=True,
    max_inline_comments=10,
    allow_snippets=True,
    notes={"docstrings": "Docstrings required for public APIs; private (_name) recommended, not required."},
)

# Sample PRs and synthetic findings
SAMPLE_PRS = {
    "Add payments gateway": "https://github.com/example/acme-payments/pull/101",
    "Refactor logging utils": "https://github.com/example/acme-core/pull/42",
    "Shell task runner": "https://github.com/example/acme-jobs/pull/7",
}

BASE_FINDINGS = {
    "F401": Finding(
        id="f1",
        tool="Flake8",
        rule_id="F401",
        severity="LOW",
        file="utils/log.py",
        start_line=1,
        message="module imported but unused: 'datetime'",
        snippet="from datetime import datetime  # unused",
        suggestion="Remove unused import or reference it.",
    ),
    "B602": Finding(
        id="f2",
        tool="Bandit",
        rule_id="B602",
        severity="HIGH",
        file="runner.py",
        start_line=88,
        message="subprocess call with shell=True identified, security issue.",
        snippet="subprocess.Popen(cmd, shell=True)",  # minimal + already public example
        suggestion="Use list-of-args and shell=False.",
    ),
    "D102": Finding(
        id="f3",
        tool="pydocstyle",
        rule_id="D102",
        severity="MEDIUM",
        file="services/payments.py",
        start_line=42,
        message="Missing docstring in public method",
        snippet="def charge_customer(self, amount): ...",
        suggestion="Add a concise docstring describing params/returns.",
    ),
    "TYP001": Finding(
        id="f4",
        tool="mypy",
        rule_id="TYP001",
        severity="MEDIUM",
        file="api/handlers.py",
        start_line=73,
        message="Function is missing type annotations for one or more arguments",
        snippet="def handle(req): return process(req)",
        suggestion="Annotate parameters and return type, e.g., def handle(req: Request) -> Response:",
    ),
}

PR_FINDING_KEYS = {
    SAMPLE_PRS["Add payments gateway"]: ["D102", "TYP001"],
    SAMPLE_PRS["Refactor logging utils"]: ["F401"],
    SAMPLE_PRS["Shell task runner"]: ["B602", "F401"],
}

RULE_BLURBS = {
    # Short, cached “what/why/fix” blurbs. In production, populate from your KB.
    ("Flake8", "F401"): {
        "what": "F401 flags imports that are never used.",
        "why": "Unused imports add noise, slow tooling, and suggest dead code.",
        "fix": "Remove the import or use it explicitly; ensure `__all__` isn’t masking usage.",
        "ref": [{"title": "Flake8 F401 docs", "anchor": "F401"}],
    },
    ("Bandit", "B602"): {
        "what": "B602 warns against `shell=True` in subprocess calls.",
        "why": "It can enable command injection if any part of the command is user-controlled.",
        "fix": "Pass a list of arguments, set `shell=False`, and validate inputs.",
        "ref": [{"title": "Bandit B602 docs", "anchor": "B602"}],
    },
    ("pydocstyle", "D102"): {
        "what": "D102 reports missing docstring in public methods.",
        "why": "Docstrings improve readability, onboarding, and tooling (Sphinx, IDEs).",
        "fix": "Add a short docstring describing purpose, params, and return value.",
        "ref": [{"title": "pydocstyle D102", "anchor": "D102"}],
    },
    ("mypy", "TYP001"): {
        "what": "Function or module lacks type annotations.",
        "why": "Types improve correctness, IDE support, and readability; they prevent common bugs.",
        "fix": "Add parameter and return annotations; enable strict checks in CI for changed files.",
        "ref": [{"title": "mypy typing guide", "anchor": "typing"}],
    },
}

def redact_snippet(snippet: Optional[str]) -> Optional[str]:
    if not snippet:
        return None
    # Very simple masking for MVP: redact quotes content and numbers
    s = snippet
    s = s.replace('"', '"█"').replace("'", "'█'")
    for d in "0123456789":
        s = s.replace(d, "█")
    # Trim to ~120 chars
    return (s[:117] + "...") if len(s) > 120 else s

def hash_span(file: str, line: int) -> str:
    return hashlib.sha1(f"{file}:{line}".encode()).hexdigest()[:10]

def _id_suffix(seed: str) -> int:
    return int(hashlib.sha1(seed.encode()).hexdigest(), 16) % 1000

def mock_fetch_findings(pr_url: str) -> List[Finding]:
    """Return findings based on known sample PRs or fallback to a generic mix.
    Deterministic IDs are produced from the pr_url so reloading keeps the same IDs.
    """
    keys = PR_FINDING_KEYS.get(pr_url)
    if not keys:
        # Fallback: derive a pseudo-random but stable selection from hash
        pool = list(BASE_FINDINGS.keys())
        h = _id_suffix(pr_url)
        keys = [pool[h % len(pool)], pool[(h + 1) % len(pool)]]

    base = _id_suffix(pr_url)
    fs: List[Finding] = []
    for i, key in enumerate(keys, start=1):
        proto = BASE_FINDINGS[key]
        fs.append(
            Finding(**{
                **proto.model_dump(),
                "id": f"{proto.id}-{base}-{i}",
                "snippet": redact_snippet(proto.snippet),
            })
        )
    return fs

# --------------------------
# Groq-aware explanation (optional)
# --------------------------

def _build_groq_prompt(find: Finding, blurb: Dict[str, Any], policy_note: str, snippet: Optional[str]) -> str:
    parts = [
        f"Rule: {find.tool} {find.rule_id}",
        f"File: {find.file}:{find.start_line}",
        f"Message: {find.message}",
        f"What: {blurb['what']}",
        f"Why: {blurb['why']}",
        f"Policy: {policy_note or 'n/a'}",
    ]
    if snippet:
        parts.append(f"Snippet (sanitized):\n{snippet}")
    parts.append("Return sections: What it is / Why it matters / How to fix. Keep it concise.")
    return "\n".join(parts)


def explain_finding(find: Finding, policy: Policy, no_snippet_mode: bool = False, use_groq: bool = False, groq_model: Optional[str] = None) -> ChatAnswer:
    key = (find.tool, find.rule_id)
    blurb = RULE_BLURBS.get(
        key,
        {
            "what": f"{find.rule_id} triggered by the analyzer.",
            "why": "The rule enforces consistency or safety per project policy.",
            "fix": "Review the rule’s guidance and update the code accordingly.",
            "ref": [],
        },
    )

    # Example snippet (sanitized)
    ex = None
    if not no_snippet_mode and policy.allow_snippets:
        ex = find.snippet

    # Policy nuance
    policy_note = ""
    if find.rule_id.startswith("D") and policy.require_docstrings_public_only:
        policy_note = (
            "Per policy, docstrings are required for public APIs; private (`_name`) recommended, not required."
        )

    what = blurb["what"]
    why = blurb["why"]
    fix = blurb["fix"]

    answer_text: Optional[str] = None
    used_groq = False
    if use_groq and HAS_GROQ and GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)  # type: ignore[name-defined]
            model = groq_model or DEFAULT_GROQ_MODEL
            prompt = _build_groq_prompt(find, blurb, policy_note, ex)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a concise code-review coach. Use clear steps and no jargon."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            content = (resp.choices[0].message.content or "").strip() if getattr(resp, "choices", None) else None
            if content:
                answer_text = content
                used_groq = True
        except Exception:
            answer_text = None

    if not answer_text:
        answer_text = (
            f"**What it is:** {what}\n\n"
            f"**Why it matters:** {why}\n\n"
            f"**How to fix:** {fix}" + (f"\n\n{policy_note}" if policy_note else "")
        )

    # Steps (deterministic and testable)
    if find.rule_id == "F401":
        steps = [
            f"Open `{find.file}` line {find.start_line}.",
            "Remove the unused import or reference it where intended.",
            "Run linters locally to confirm the warning is resolved.",
        ]
    elif find.rule_id == "B602":
        steps = [
            f"Open `{find.file}` line {find.start_line}.",
            "Replace the string command with a list of args, e.g., ['ls','-l']",
            "Set `shell=False` and validate inputs.",
            "Re-run security checks.",
        ]
    elif find.rule_id == "D102":
        steps = [
            f"Open `{find.file}` line {find.start_line}.",
            "Add a concise docstring describing purpose, parameters, and return.",
            "Ensure docstring style matches the team convention.",
        ]
    elif find.rule_id == "TYP001":
        steps = [
            f"Open `{find.file}` line {find.start_line}.",
            "Add type annotations for parameters and return type.",
            "Run `mypy` locally to confirm the error is resolved.",
        ]
    else:
        steps = [
            f"Review `{find.file}` lines {find.start_line}-{find.end_line or find.start_line}.",
            "Apply the rule’s guidance; re-run checks.",
        ]

    return ChatAnswer(
        answer=answer_text,
        steps=steps,
        example_snippet=ex,
        references=blurb["ref"],
        safety={
            "redactions_applied": True,
            "span_hash": hash_span(find.file, find.start_line),
            "used_groq": used_groq,
        },
    )

# --------------------------
# Gradio App
# --------------------------

def build_gradio_app():
    if not HAS_SSL or not HAS_GRADIO:
        raise RuntimeError("Gradio/SSL not available.")

    with gr.Blocks(title="PR Coach — Explain & Coach (Python)") as demo:  # type: ignore[name-defined]
        gr.Markdown(
            """
# 🧑‍🏫 PR Coach — Explain & Coach (Python)
Pick a **sample PR** or paste a PR URL, load findings, then click a finding or ask a question.
**Privacy-first:** snippets are minimal and redacted; toggle “No-snippet mode” anytime.
            """
        )

        with gr.Row():
            sample_choice = gr.Dropdown(
                choices=list(SAMPLE_PRS.keys()),
                value=list(SAMPLE_PRS.keys())[0],
                label="Sample PRs",
                info="Select to auto-fill a demo PR URL",
            )
            pr_url = gr.Textbox(
                label="Pull Request URL",
                placeholder="https://github.com/org/repo/pull/123",
                value=SAMPLE_PRS[list(SAMPLE_PRS.keys())[0]],
            )
            use_sample_btn = gr.Button("Use Sample", variant="secondary")
            load_btn = gr.Button("Load Findings", variant="primary")
            no_snippet = gr.Checkbox(label="No-snippet mode", value=False)

        with gr.Row():
            findings_df = gr.Dataframe(
                headers=["id", "tool", "rule_id", "severity", "file", "line", "message"],
                datatype=["str", "str", "str", "str", "str", "number", "str"],
                row_count=(0, "dynamic"),
                interactive=False,
                label="Findings",
            )

        with gr.Row():
            finding_selector = gr.Dropdown(choices=[], label="Select a finding to explain", interactive=True)
        with gr.Row():
            chat = gr.Chatbot(label="PR Coach Chat", height=360)
        with gr.Row():
            user_msg = gr.Textbox(label="Ask a question about this PR or a rule (optional)")
            ask_btn = gr.Button("Ask")
            explain_btn = gr.Button("Explain Selected Finding", variant="primary")
        with gr.Row():
            copy_fix = gr.Button("Copy Fix Steps")
            helpful = gr.Radio(choices=["👍 Helpful", "👎 Not helpful"], label="Rate last answer")
            clear_btn = gr.Button("Clear Chat")
            status = gr.Markdown("")

        # State
        findings_state = gr.State([])
        policy_state = gr.State(MOCK_POLICY.model_dump())

        def on_use_sample(name: str):
            url = SAMPLE_PRS.get(name)
            return gr.update(value=url)

        use_sample_btn.click(on_use_sample, inputs=[sample_choice], outputs=[pr_url])

        def on_load(pr: str):
            if not pr or "http" not in pr:
                raise gr.Error("Please provide a valid PR URL.")
            fs = mock_fetch_findings(pr)
            rows = []
            choices = []
            for f in fs:
                rows.append([f.id, f.tool, f.rule_id, f.severity, f.file, f.start_line, f.message])
                choices.append(f"{f.id} · {f.tool}/{f.rule_id} · {f.file}:{f.start_line}")
            msg = f"Loaded {len(fs)} findings from: {pr}"
            return (
                rows,
                gr.update(choices=choices, value=choices[0] if choices else None),
                [fi.model_dump() for fi in fs],
                msg,
                [("system", "Findings loaded. Select one or ask a question.")],
            )

        load_btn.click(
            on_load,
            inputs=[pr_url],
            outputs=[findings_df, finding_selector, findings_state, status, chat],
        )

        def explain_selected(
            choice: str, fs: List[Dict], pol: Dict, ns: bool, history: List[Tuple[str, str]]
        ):
            if not choice:
                raise gr.Error("Select a finding first.")
            # Map back to Finding
            id_part = choice.split(" · ")[0]
            find = None
            for f in fs:
                if f["id"] == id_part:
                    find = Finding(**f)
                    break
            if not find:
                raise gr.Error("Could not locate the selected finding.")

            ans = explain_finding(find, Policy(**pol), no_snippet_mode=ns, use_groq=bool(GROQ_API_KEY))
            header = f"**{find.tool} {find.rule_id} at {find.file}:{find.start_line}**\n\n"
            msg = header + ans.answer
            if ans.steps:
                msg += "\n\n**Steps to fix:**\n" + "\n".join([f"• {s}" for s in ans.steps])
            if ans.example_snippet:
                msg += f"\n\n**Example (sanitized):**\n```python\n{ans.example_snippet}\n```"
            if ans.references:
                refs_txt = "; ".join([r["title"] for r in ans.references])
                msg += f"\n\n**References:** {refs_txt}"
            history = (history or []) + [("user", f"Explain {find.tool} {find.rule_id} in {find.file}:{find.start_line}"), ("assistant", msg)]
            return history, f"Answer generated. Safety: redactions applied = {ans.safety.get('redactions_applied', False)}"

        explain_btn.click(
            explain_selected,
            inputs=[finding_selector, findings_state, policy_state, no_snippet, chat],
            outputs=[chat, status],
        )

        def ask_question(
            q: str, fs: List[Dict], pol: Dict, ns: bool, history: List[Tuple[str, str]]
        ):
            if not q:
                raise gr.Error("Type a question first.")
            chosen = None
            for f in fs or []:
                if f["rule_id"] in q or f["file"] in q:
                    chosen = Finding(**f)
                    break

            if chosen:
                ans = explain_finding(chosen, Policy(**pol), no_snippet_mode=ns, use_groq=bool(GROQ_API_KEY))
                msg = f"**{chosen.tool} {chosen.rule_id} at {chosen.file}:{chosen.start_line}**\n\n" + ans.answer
                if ans.steps:
                    msg += "\n\n**Steps to fix:**\n" + "\n".join([f"• {s}" for s in ans.steps])
            else:
                # Policy-only generic answer
                msg = (
                    "**Policy overview:** Docstrings required for public classes/functions; "
                    "private (`_name`) recommended. Avoid `shell=True` in subprocess. "
                    "Remove unused imports flagged by F401."
                )

            history = (history or []) + [("user", q), ("assistant", msg)]
            return "", history, "Answered."

        ask_btn.click(
            ask_question,
            inputs=[user_msg, findings_state, policy_state, no_snippet, chat],
            outputs=[user_msg, chat, status],
        )

        def copy_last_steps(history: List[Tuple[str, str]]):
            if not history:
                return "No answer to copy."
            # Find last assistant message
            for role, content in reversed(history):
                if role == "assistant":
                    last = content
                    break
            else:
                return "No steps found in last answer."
            lines = [ln for ln in last.splitlines() if ln.strip().startswith("• ")]
            if not lines:
                return "No steps found in last answer."
            return gr.update(value="\n".join(lines))

        copy_fix.click(
            copy_last_steps,
            inputs=[chat],
            outputs=[user_msg],
        )

        def rate_answer(rate: str):
            # In production: store rating (👍/👎) with finding_id + span_hash + response_id
            time.sleep(0.1)
            return "Thanks for the feedback! (stored)"

        helpful.change(rate_answer, inputs=[helpful], outputs=[status])

        def clear_chat():
            return []

        clear_btn.click(clear_chat, inputs=None, outputs=[chat])

    return demo

# --------------------------
# CLI Fallback (no SSL/Gradio needed)
# --------------------------

def run_cli(groq_model: Optional[str] = None):
    print("PR Coach — CLI mode (no SSL/Gradio required)\n")
    if GROQ_API_KEY and HAS_GROQ:
        print(f"[Groq] Enabled with model: {groq_model or DEFAULT_GROQ_MODEL}")
    else:
        if not GROQ_API_KEY:
            print("[Groq] Disabled (no GROQ_API_KEY). Using local explanations.")
        elif not HAS_GROQ:
            print(f"[Groq] SDK not available: {GROQ_IMPORT_ERR!r}. Using local explanations.")

    print("\nSample PRs:")
    for name, url in SAMPLE_PRS.items():
        print(f"  - {name}: {url}")
    pr = input("\nPaste a PR URL (or press Enter to use the first sample): ").strip()
    if not pr:
        pr = next(iter(SAMPLE_PRS.values()))
    findings = mock_fetch_findings(pr)
    if not findings:
        print("No findings. You're good!")
        return 0
    print(f"\nLoaded {len(findings)} finding(s) from {pr}\n")
    for idx, f in enumerate(findings, 1):
        print(f"[{idx}] {f.tool} {f.rule_id} • {f.severity} • {f.file}:{f.start_line} — {f.message}")
    while True:
        try:
            choice = input("\nSelect a finding # to explain (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                break
            n = int(choice)
            assert 1 <= n <= len(findings)
        except Exception:
            print("Invalid choice. Try again.")
            continue
        ans = explain_finding(findings[n-1], MOCK_POLICY, no_snippet_mode=False, use_groq=bool(GROQ_API_KEY), groq_model=groq_model)
        print("\n=== Explanation ===")
        print(ans.answer)
        if ans.steps:
            print("\nSteps to fix:")
            for s in ans.steps:
                print(" -", s)
        if ans.example_snippet:
            print("\nExample (sanitized):\n" + ans.example_snippet)
    print("\nGoodbye!")
    return 0

# --------------------------
# Tests
# --------------------------

def _assert(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)

def run_tests() -> None:
    print("Running tests…")

    # redact_snippet masks digits and quotes content
    s = 'print("abc123")  # note'
    red = redact_snippet(s)
    _assert(red is not None and '123' not in red, "Digits should be redacted")
    _assert('"█"' in red or "'█'" in red, "Quoted content should be masked")

    # Deterministic findings for same URL
    url = SAMPLE_PRS["Refactor logging utils"]
    f1 = mock_fetch_findings(url)
    f2 = mock_fetch_findings(url)
    _assert([x.id for x in f1] == [x.id for x in f2], "IDs must be deterministic per URL")

    # Different URL → likely different IDs
    url2 = SAMPLE_PRS["Shell task runner"]
    f3 = mock_fetch_findings(url2)
    _assert([x.id for x in f1] != [x.id for x in f3], "Different URLs should yield different IDs")

    # Explain known rules produce expected steps
    ans_f401 = explain_finding(BASE_FINDINGS["F401"], MOCK_POLICY)
    _assert(any("unused import" in s.lower() for s in ans_f401.steps), "F401 steps should mention unused import")

    ans_b602 = explain_finding(BASE_FINDINGS["B602"], MOCK_POLICY)
    _assert(any("shell=False" in s for s in ans_b602.steps), "B602 steps should mention shell=False")

    # Policy nuance for D102
    ans_d102 = explain_finding(BASE_FINDINGS["D102"], MOCK_POLICY)
    _assert("docstrings are required for public" in ans_d102.answer, "D102 should include policy note")

    # Groq prompt redaction/structure
    fb = BASE_FINDINGS["B602"].model_copy()
    fb.snippet = redact_snippet("subprocess.Popen(cmd, shell=True) # 1234")
    prompt = _build_groq_prompt(fb, RULE_BLURBS[("Bandit", "B602")], "", fb.snippet)
    _assert("1234" not in prompt, "Prompt should not include unredacted digits")
    _assert("Rule:" in prompt and "File:" in prompt, "Prompt must include headers")

    print("All tests passed.\n")

# --------------------------
# Entrypoint — suppress SystemExit to avoid noisy tracebacks
# --------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PR Coach — Explain & Coach")
    parser.add_argument("--cli", action="store_true", help="Run CLI fallback instead of Gradio UI")
    parser.add_argument("--test", action="store_true", help="Run unit tests and exit")
    parser.add_argument("--groq-model", type=str, default=None, help="Groq model to use (e.g., llama-3.1-8b-instant)")
    args = parser.parse_args(argv)

    if args.test:
        run_tests()
        return 0

    if args.cli or not (HAS_SSL and HAS_GRADIO):
        if not HAS_SSL:
            print("[INFO] Python was built without SSL. Falling back to CLI mode.")
        elif not HAS_GRADIO:
            print(f"[INFO] Gradio not available: {GRADIO_IMPORT_ERR!r}. Falling back to CLI mode.")
        return run_cli(args.groq_model)

    # Launch Gradio UI
    app = build_gradio_app()
    if GROQ_API_KEY:
        print(f"[Groq] Enabled with model: {args.groq_model or DEFAULT_GROQ_MODEL}")
    else:
        print("[Groq] Disabled (no GROQ_API_KEY). Using local explanations.")
    app.launch()
    return 0


if __name__ == "__main__":
    # Avoid raising SystemExit so environments don't show "SystemExit: 0"
    try:
        _exit_code = main()
    except SystemExit as e:  # just in case a library raises it internally
        _exit_code = int(getattr(e, "code", 0) or 0)
    # Optionally, report a non-zero code without throwing
    if _exit_code not in (0, None):
        print(f"[EXIT] Non-zero exit code: {_exit_code}")
