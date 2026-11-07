#!/usr/bin/env python3
"""Lint prose with locally installed SlopSift and Vale, and normalize the findings.

This adapter never installs or downloads anything. It runs only binaries that
are already on the machine, passes SlopSift --no-download so it cannot fetch a
model, and reports a missing tool or a failed run as such, never as a clean
result.

Inputs:
  .md .mdx .markdown .txt .text .rst .adoc .html .htm   linted as-is
  .pptx   slide copy and speaker notes extracted and linted as two documents
  .docx   body text extracted and linted as one document
  -       read text from stdin

Tools (default: both):
  slopsift  $SLOPSIFT_BIN, then node_modules/.bin/slopsift in the current or a
            parent directory, then `slopsift` on PATH
  vale      $VALE_BIN, then `vale` on PATH. Uses the project's .vale.ini when
            Vale finds one, else the minimal config bundled in assets/vale/.

Output (--format json, the default) is one JSON object:
  status    "clean" | "findings" | "incomplete"
  tools     one entry per requested tool: status ok | missing | failed, the
            command, exit code, version, and stderr
  findings  file, part, location, tool, rule, severity, message, text, and the
            tool's original diagnostic under "original"

Exit codes:
  0   every requested tool ran and reported nothing
  1   every requested tool ran and at least one reported a finding
  2   at least one requested tool was missing or failed (other tools' findings
      are still reported); this is never a clean result
  64  usage error (bad arguments, unreadable or unsupported input)

Usage:
  python3 scripts/lint.py draft.md
  python3 scripts/lint.py deck.pptx --tool slopsift --level warning
  pbpaste | python3 scripts/lint.py - --format text
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

SCHEMA = "write-lint/1"
SKILL_DIR = Path(__file__).resolve().parent.parent
BUNDLED_VALE_CONFIG = SKILL_DIR / "assets" / "vale" / ".vale.ini"
TOOLS = ("slopsift", "vale")
TEXT_EXTS = {".md", ".mdx", ".markdown", ".txt", ".text", ".rst", ".adoc", ".html", ".htm"}
TIMEOUT = int(os.environ.get("WRITE_LINT_TIMEOUT", "300"))
SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"lint.py: error: {message}", file=sys.stderr)
        sys.exit(64)


# --- documents ---------------------------------------------------------------


class Document:
    """One unit of text handed to the linters.

    `source` is what the user passed, `part` names the extracted piece of a
    container format (slides, notes, body), `path` is the file the tools read,
    and `line_map` maps a 1-based line in `path` to a slide number.
    """

    def __init__(self, source, path, part=None, line_map=None):
        self.source = source
        self.path = Path(path).resolve()
        self.part = part
        self.line_map = line_map or {}

    def describe(self):
        d = {"file": self.source, "part": self.part}
        if self.part is None and self.source != "-":
            d["linted_as"] = str(self.path)
        else:
            d["extracted"] = True
        return d


def _paragraph_text(par, ns):
    return "".join(t.text or "" for t in par.iter(f"{ns}t")).strip()


def _write_parts(tmp, stem, part, blocks):
    """Write [(slide_or_None, [paragraph, ...]), ...] to a .md file with a line map."""
    lines, line_map = [], {}
    for slide, paras in blocks:
        paras = [p for p in paras if p]
        if not paras:
            continue
        for p in paras:
            for physical in p.splitlines() or [""]:
                lines.append(physical)
                if slide is not None:
                    line_map[len(lines)] = slide
            lines.append("")
    path = Path(tmp) / f"{stem}.{part}.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path, line_map


def _rels(z, rels_path):
    try:
        root = ElementTree.fromstring(z.read(rels_path))
    except KeyError:
        return {}
    return {r.get("Id"): r for r in root.iter(f"{NS_REL}Relationship")}


def _resolve(base_dir, target):
    parts = []
    for seg in (base_dir + "/" + target).split("/"):
        if seg == "..":
            if parts:
                parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def extract_pptx(src, tmp):
    """Return (slides_path, slides_map, notes_path, notes_map) for a .pptx."""
    try:
        z = zipfile.ZipFile(src)
    except (zipfile.BadZipFile, OSError) as e:
        raise UsageError(f"{src}: not a readable .pptx ({e})")
    with z:
        try:
            pres = ElementTree.fromstring(z.read("ppt/presentation.xml"))
        except KeyError:
            raise UsageError(f"{src}: no ppt/presentation.xml; not a PowerPoint file")
        pres_rels = _rels(z, "ppt/_rels/presentation.xml.rels")
        slide_files = []
        for sid in pres.iter(f"{NS_P}sldId"):
            rel = pres_rels.get(sid.get(f"{NS_R}id"))
            if rel is not None:
                slide_files.append(_resolve("ppt", rel.get("Target")))

        slides, notes = [], []
        for n, sfile in enumerate(slide_files, start=1):
            root = ElementTree.fromstring(z.read(sfile))
            slides.append((n, [_paragraph_text(p, NS_A) for p in root.iter(f"{NS_A}p")]))
            sdir, sname = sfile.rsplit("/", 1)
            for rel in _rels(z, f"{sdir}/_rels/{sname}.rels").values():
                if rel.get("Type", "").endswith("/notesSlide"):
                    nfile = _resolve(sdir, rel.get("Target"))
                    nroot = ElementTree.fromstring(z.read(nfile))
                    paras = []
                    for sp in nroot.iter(f"{NS_P}sp"):
                        ph = sp.find(f".//{NS_P}ph")
                        # Only the notes body; skip the slide image, number, and header placeholders.
                        if ph is None or ph.get("type") != "body":
                            continue
                        paras += [_paragraph_text(p, NS_A) for p in sp.iter(f"{NS_A}p")]
                    notes.append((n, paras))
    stem = Path(src).stem
    spath, smap = _write_parts(tmp, stem, "slides", slides)
    npath, nmap = _write_parts(tmp, stem, "notes", notes)
    return spath, smap, npath, nmap


def extract_docx(src, tmp):
    try:
        with zipfile.ZipFile(src) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
    except (zipfile.BadZipFile, OSError, KeyError) as e:
        raise UsageError(f"{src}: not a readable .docx ({e})")
    paras = [_paragraph_text(p, NS_W) for p in root.iter(f"{NS_W}p")]
    path, _ = _write_parts(tmp, Path(src).stem, "body", [(None, paras)])
    return path


def collect(inputs, tmp):
    docs = []
    for raw in inputs:
        if raw == "-":
            path = Path(tmp) / "stdin.md"
            path.write_text(sys.stdin.read(), encoding="utf-8")
            docs.append(Document("-", path))
            continue
        src = Path(raw)
        if not src.is_file():
            raise UsageError(f"{raw}: no such file")
        ext = src.suffix.lower()
        if ext == ".pptx":
            spath, smap, npath, nmap = extract_pptx(src, tmp)
            docs.append(Document(raw, spath, "slides", smap))
            docs.append(Document(raw, npath, "notes", nmap))
        elif ext == ".docx":
            docs.append(Document(raw, extract_docx(src, tmp), "body"))
        elif ext in TEXT_EXTS:
            docs.append(Document(raw, src))
        else:
            raise UsageError(
                f"{raw}: unsupported file type {ext or '(none)'}; export it to "
                ".md or .txt first (supported: " + ", ".join(sorted(TEXT_EXTS | {'.pptx', '.docx'})) + ")"
            )
    return docs


# --- running tools -------------------------------------------------------------


def find_slopsift():
    env = os.environ.get("SLOPSIFT_BIN")
    if env:
        return env if Path(env).is_file() else None
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        local = d / "node_modules" / ".bin" / "slopsift"
        if local.is_file():
            return str(local)
    return shutil.which("slopsift")


def find_vale():
    env = os.environ.get("VALE_BIN")
    if env:
        return env if Path(env).is_file() else None
    return shutil.which("vale")


INSTALL_HINT = {
    "slopsift": "Install it yourself if you want it, e.g. `npm install --save-dev slopsift` "
                "(Node.js 24+), or set SLOPSIFT_BIN. This script does not install it.",
    "vale": "Install it yourself if you want it, e.g. `brew install vale` or a release from "
            "https://github.com/errata-ai/vale/releases, or set VALE_BIN. This script does not install it.",
}


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    except FileNotFoundError as e:
        return None, f"could not execute: {e}"
    except PermissionError as e:
        return None, f"could not execute: {e}"
    except subprocess.TimeoutExpired:
        return None, f"timed out after {TIMEOUT}s"
    except OSError as e:
        return None, f"could not execute: {e}"
    return p, None


def version_of(binary):
    p, _ = run([binary, "--version"])
    if p is None or p.returncode != 0:
        return None
    out = (p.stdout or p.stderr).strip().splitlines()
    return out[0] if out else None


def tool_record(tool, status, **kw):
    rec = {"tool": tool, "status": status}
    rec.update({k: v for k, v in kw.items() if v is not None})
    return rec


def slot_for(docs, reported_path, cwd):
    p = Path(reported_path)
    if not p.is_absolute():
        p = Path(cwd) / p
    p = p.resolve()
    for d in docs:
        if d.path == p:
            return d
    return None


def normalize(doc, tool, rule, severity, message, text, line, column, end_line, end_column, original):
    loc = {"line": line, "column": column}
    if end_line is not None:
        loc["end_line"] = end_line
    if end_column is not None:
        loc["end_column"] = end_column
    slide = doc.line_map.get(line) if doc and line else None
    if slide is not None:
        loc["slide"] = slide
    return {
        "file": doc.source if doc else None,
        "part": doc.part if doc else None,
        "location": loc,
        "tool": tool,
        "rule": rule,
        "severity": severity,
        "message": message,
        "text": text,
        "original": original,
    }


SLOPSIFT_LEVEL = {"info": "info", "warning": "warning", "error": "error"}
SLOPSIFT_SEVERITY = {"error": "error", "warn": "warning", "warning": "warning", "info": "info"}


def run_slopsift(docs, level):
    binary = find_slopsift()
    if not binary:
        return tool_record("slopsift", "missing", note=INSTALL_HINT["slopsift"]), []
    cmd = [binary, *[str(d.path) for d in docs],
           "--rulepack", "ai-style", "--rulepack", "reader-first",
           "--level", SLOPSIFT_LEVEL[level], "--format", "json",
           "--exit-zero", "--no-ignore", "--no-download"]
    p, err = run(cmd)
    base = {"binary": binary, "command": cmd}
    if p is None:
        return tool_record("slopsift", "failed", error=err, **base), []
    base.update(exit_code=p.returncode, stderr=p.stderr.strip() or None, version=version_of(binary))
    if p.returncode != 0:
        return tool_record("slopsift", "failed", error=f"exited {p.returncode}", **base), []
    try:
        results = json.loads(p.stdout)
        if not isinstance(results, list):
            raise ValueError("expected a JSON array")
    except ValueError as e:
        return tool_record("slopsift", "failed", error=f"unreadable JSON output: {e}",
                           stdout=p.stdout[:2000], **base), []
    findings = []
    cwd = os.getcwd()
    for fr in results:
        doc = slot_for(docs, fr.get("filePath", ""), cwd)
        for m in fr.get("messages", []):
            findings.append(normalize(
                doc, "slopsift", m.get("ruleId"),
                SLOPSIFT_SEVERITY.get(m.get("level"), "info"),
                m.get("message"), m.get("text"),
                m.get("line"), m.get("column"), m.get("endLine"), m.get("endColumn"), m,
            ))
    return tool_record("slopsift", "ok", **base), findings


VALE_LEVEL = {"info": "suggestion", "warning": "warning", "error": "error"}
VALE_SEVERITY = {"error": "error", "warning": "warning", "suggestion": "info"}


def _vale_once(binary, docs, level, config):
    cmd = [binary, "--output=JSON", f"--minAlertLevel={VALE_LEVEL[level]}", "--no-exit"]
    if config:
        cmd.append(f"--config={config}")
    cmd += [str(d.path) for d in docs]
    p, err = run(cmd)
    return cmd, p, err


def _vale_json(p):
    """Alerts from stdout, or Vale's runtime-error object, which it writes to stderr."""
    if p is None:
        return None
    if p.stdout.strip():
        try:
            return json.loads(p.stdout)
        except ValueError:
            return None
    if p.stderr.strip():
        try:
            data = json.loads(p.stderr)
            if isinstance(data, dict) and "Code" in data:
                return data
        except ValueError:
            pass
        return None if p.returncode not in (0, 1) else {}
    return {}


def run_vale(docs, level, vale_config):
    binary = find_vale()
    if not binary:
        return tool_record("vale", "missing", note=INSTALL_HINT["vale"]), []
    config_source = "explicit" if vale_config else "project"
    cmd, p, err = _vale_once(binary, docs, level, vale_config)
    data = _vale_json(p)
    # E100: Vale found no .vale.ini. Fall back to the bundled minimal config.
    if not vale_config and isinstance(data, dict) and data.get("Code") == "E100":
        config_source = "bundled"
        cmd, p, err = _vale_once(binary, docs, level, str(BUNDLED_VALE_CONFIG))
        data = _vale_json(p)
    base = {"binary": binary, "command": cmd, "config": config_source}
    if p is None:
        return tool_record("vale", "failed", error=err, **base), []
    base.update(exit_code=p.returncode, stderr=p.stderr.strip() or None, version=version_of(binary))
    if not isinstance(data, dict):
        return tool_record("vale", "failed", error="unreadable JSON output",
                           stdout=p.stdout[:2000], **base), []
    if "Code" in data and "Text" in data:
        return tool_record("vale", "failed", error=f"{data['Code']}: {data['Text']}",
                           original=data, **base), []
    if p.returncode not in (0, 1):
        return tool_record("vale", "failed", error=f"exited {p.returncode}", **base), []
    findings = []
    cwd = os.getcwd()
    for path, alerts in data.items():
        doc = slot_for(docs, path, cwd)
        for a in alerts or []:
            span = a.get("Span") or [None, None]
            findings.append(normalize(
                doc, "vale", a.get("Check"),
                VALE_SEVERITY.get(a.get("Severity"), "info"),
                a.get("Message"), a.get("Match"),
                a.get("Line"), span[0], a.get("Line"), span[1], a,
            ))
    return tool_record("vale", "ok", **base), findings


# --- output -------------------------------------------------------------------


def render_text(report):
    out = []
    for t in report["tools"]:
        line = f"{t['tool']}: {t['status']}"
        if t.get("version"):
            line += f" ({t['version']})"
        if t.get("config"):
            line += f", config: {t['config']}"
        if t.get("error"):
            line += f": {t['error']}"
        if t.get("note"):
            line += f". {t['note']}"
        out.append(line)
        if t["status"] == "failed" and t.get("stderr"):
            out += ["  " + s for s in t["stderr"].splitlines()[:10]]
    out.append("")
    for f in report["findings"]:
        where = f["file"] or "?"
        if f["part"]:
            where += f"#{f['part']}"
        loc = f["location"]
        if "slide" in loc:
            where += f" slide {loc['slide']}"
        where += f":{loc.get('line')}:{loc.get('column')}"
        out.append(f"{where} {f['severity']} {f['tool']} {f['rule']}: {f['message']}")
        if f.get("text"):
            out.append(f"    \"{f['text']}\"")
    s = report["summary"]
    out.append("")
    out.append(f"status: {report['status']}, {s['findings']} finding(s) "
               f"({s['by_severity']['error']} error, {s['by_severity']['warning']} warning, "
               f"{s['by_severity']['info']} info)")
    if report["status"] == "incomplete":
        out.append("Not a clean result: at least one requested tool did not run.")
    out.append("Findings are editorial signals, not proof of AI authorship.")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = Parser(description="Lint prose with locally installed SlopSift and Vale.")
    ap.add_argument("inputs", nargs="+", metavar="PATH", help="file to lint, or - for stdin")
    ap.add_argument("--tool", action="append", choices=TOOLS,
                    help="tool to run (repeatable; default: all)")
    ap.add_argument("--level", choices=("info", "warning", "error"), default="info",
                    help="minimum severity to report (default: info)")
    ap.add_argument("--vale-config", metavar="PATH", help="explicit .vale.ini for Vale")
    ap.add_argument("--format", choices=("json", "text"), default="json")
    args = ap.parse_args(argv)
    tools = list(dict.fromkeys(args.tool or TOOLS))

    if args.vale_config and not Path(args.vale_config).is_file():
        ap.error(f"--vale-config {args.vale_config}: no such file")

    with tempfile.TemporaryDirectory(prefix="write-lint-") as tmp:
        try:
            docs = collect(args.inputs, tmp)
        except UsageError as e:
            print(f"lint.py: error: {e}", file=sys.stderr)
            return 64

        records, findings = [], []
        for tool in tools:
            if tool == "slopsift":
                rec, fs = run_slopsift(docs, args.level)
            else:
                rec, fs = run_vale(docs, args.level, args.vale_config)
            records.append(rec)
            findings += fs

    order = {(d.source, d.part): i for i, d in enumerate(docs)}
    findings.sort(key=lambda f: (
        order.get((f["file"], f["part"]), len(order)), f["location"].get("line") or 0,
        f["location"].get("column") or 0, -SEVERITY_RANK[f["severity"]], f["tool"],
    ))
    by_sev = {k: sum(1 for f in findings if f["severity"] == k) for k in ("error", "warning", "info")}
    if any(r["status"] != "ok" for r in records):
        status, code = "incomplete", 2
    elif findings:
        status, code = "findings", 1
    else:
        status, code = "clean", 0

    report = {
        "schema": SCHEMA,
        "status": status,
        "summary": {"findings": len(findings), "by_severity": by_sev, "documents": len(docs)},
        "documents": [d.describe() for d in docs],
        "tools": records,
        "findings": findings,
    }
    if args.format == "json":
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(render_text(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
