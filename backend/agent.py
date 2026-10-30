import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .nebuis_client import get_client, get_model

ALLOWED_SUFFIXES = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
MAX_FILE_BYTES = 60_000

SYSTEM_PROMPT = """You are CodePilot, a careful autonomous software engineering agent.
You are working in a temporary project workspace supplied by the user.
Use tools to do real work. Workflow:
1. Briefly plan the task.
2. Inspect files with list_files and read_file.
3. Make focused edits with write_file when appropriate.
4. For Python tasks, call run_tests after edits or test generation.
5. Read test output, fix failures if appropriate, and rerun tests.
6. Finish with a concise report of changes, actual test results, and remaining risks.
Never claim tests passed unless run_tests returned success. Use relative paths only.
Do not edit source for review/explain-only tasks unless asked. The workspace is temporary.
"""

def safe_path(root: Path, raw: str) -> Path:
    clean = raw.replace("\\", "/").strip()
    if not clean or clean.startswith("/") or re.match(r"^[A-Za-z]:", clean):
        raise ValueError("Use a relative workspace path.")
    target = (root / clean).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise ValueError("Path escapes the workspace.")
    if target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"File extension not allowed: {target.suffix or '(none)'}")
    return target

def inspect_python(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8", errors="replace")
    info = {"path": path.name, "characters": len(source)}
    try:
        tree = ast.parse(source)
        info["syntax"] = "valid"
        info["functions"] = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        info["classes"] = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        info["imports"] = [
            n.module if isinstance(n, ast.ImportFrom) else ",".join(a.name for a in n.names)
            for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
        ][:30]
    except SyntaxError as exc:
        info["syntax"] = "error"
        info["syntax_error"] = f"line {exc.lineno}: {exc.msg}"
    return info

def run_agent(task: str, task_type: str, files: list[dict[str, str]]) -> dict[str, Any]:
    client, model = get_client(), get_model()
    max_steps = max(1, min(int(os.getenv("MAX_AGENT_STEPS", "8")), 12))
    events: list[dict[str, str]] = []
    changed: list[str] = []
    tool_results: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="codepilot-") as tmp:
        root = Path(tmp).resolve()
        for item in files:
            target = safe_path(root, item["path"])
            if len(item["content"].encode("utf-8")) > MAX_FILE_BYTES:
                raise ValueError(f"{item['path']} exceeds 60 KB.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item["content"], encoding="utf-8")

        def list_files(**kwargs):
            return {"files": [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()][:100]}

        def read_file(path: str, **kwargs):
            target = safe_path(root, path)
            if not target.exists():
                return {"error": f"{path} does not exist"}
            data = {"path": path, "content": target.read_text(encoding="utf-8", errors="replace")[:30000]}
            if target.suffix == ".py":
                data["static_analysis"] = inspect_python(target)
            return data

        def write_file(path: str, content: str, **kwargs):
            target = safe_path(root, path)
            if len(content.encode("utf-8")) > MAX_FILE_BYTES:
                return {"error": "File exceeds 60 KB."}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            rel = str(target.relative_to(root))
            if rel not in changed:
                changed.append(rel)
            events.append({"kind": "edit", "message": f"Updated {rel}", "detail": "Agent wrote a workspace file."})
            return {"ok": True, "path": rel, "characters": len(content)}

        def run_tests(**kwargs):
            if not list(root.rglob("*.py")):
                return {"ok": False, "summary": "No Python files found."}
            # Local hackathon demo only: pytest executes workspace Python code.
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q"], cwd=root,
                    capture_output=True, text=True, timeout=12,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
                )
                output = (proc.stdout + "\n" + proc.stderr).strip()[-7000:]
                return {"ok": proc.returncode == 0, "exit_code": proc.returncode,
                        "summary": output or "Pytest completed without output."}
            except subprocess.TimeoutExpired:
                return {"ok": False, "summary": "Tests timed out after 12 seconds."}

        tool_map = {"list_files": list_files, "read_file": read_file,
                    "write_file": write_file, "run_tests": run_tests}
        tools = [
            {"type": "function", "function": {"name": "list_files", "description": "List workspace files.", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "read_file", "description": "Read a workspace file. Python files include AST analysis.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "write_file", "description": "Create or replace a workspace file. Allowed extensions: py, md, txt, json, toml, yaml, yml, ini, cfg.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
            {"type": "function", "function": {"name": "run_tests", "description": "Run pytest in the temporary workspace. Only for trusted Python code.", "parameters": {"type": "object", "properties": {}, "required": []}}}
        ]
        events.append({"kind": "plan", "message": "Agent started", "detail": f"Task type: {task_type}"})
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task type: {task_type}\nUser request: {task}\nInspect the supplied workspace and complete the task. Use tools to make and verify changes."}
        ]
        final_text = ""
        for step in range(max_steps):
            events.append({"kind": "thinking", "message": f"Agent step {step + 1}", "detail": "Calling NVIDIA Nemotron through Nebius Token Factory."})
            response = client.chat.completions.create(
                model=model, messages=messages, tools=tools, tool_choice="auto",
                temperature=0.2, max_tokens=3500
            )
            msg = response.choices[0].message
            assistant = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant["tool_calls"] = [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in msg.tool_calls
                ]
            messages.append(assistant)
            if not msg.tool_calls:
                final_text = msg.content or "Agent finished without a final report."
                break
            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                    result = tool_map[name](**args) if name in tool_map else {"error": "Unknown tool"}
                except Exception as exc:
                    result = {"error": str(exc)}
                tool_results.append({"tool": name, "result": json.dumps(result, ensure_ascii=False)[:8000]})
                events.append({"kind": "tool", "message": f"Tool: {name}", "detail": str(result)[:500]})
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result, ensure_ascii=False)[:8000]})
        else:
            final_text = "Agent reached the maximum tool-call steps. Review activity and run again if needed."

        output_files = []
        for path in root.rglob("*"):
            if path.is_file():
                output_files.append({"path": str(path.relative_to(root)),
                                     "content": path.read_text(encoding="utf-8", errors="replace")[:30000]})
        events.append({"kind": "done", "message": "Workflow finished", "detail": f"{len(changed)} file(s) changed."})
        return {"summary": final_text, "events": events, "changed_files": changed,
                "files": output_files, "tool_results": tool_results, "model": model}

def direct_analysis(task_type: str, code: str, language: str) -> str:
    client = get_client()
    prompts = {
        "review": "Review correctness, maintainability, performance, and security. Prioritize findings.",
        "debug": "Find likely bugs, explain root causes, and show a corrected version.",
        "tests": "Generate useful unit tests. For Python, provide executable pytest tests.",
        "explain": "Explain the code flow, important functions, and edge cases for a junior developer.",
        "build": "Propose an implementation plan and starter code for the requested feature."
    }
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": "You are CodePilot, an expert software engineer. Be specific. Never claim code was executed."},
            {"role": "user", "content": f"{prompts.get(task_type, prompts['review'])}\nLanguage: {language}\n\n```{language}\n{code}\n```"}
        ],
        temperature=0.2, max_tokens=3000
    )
    return response.choices[0].message.content or "No response returned."
