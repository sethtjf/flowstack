#!/usr/bin/env python3
"""Tests for lint.py's success, findings, missing-tool, and failure paths.

The tests use small fake `slopsift` and `vale` executables, so they need only
python3 and run anywhere, including CI without either tool installed.

Usage: python3 scripts/test_lint.py
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

# Keep the skill folder byte-identical to its plugin copies (validate.sh diffs them).
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
LINT = HERE / "lint.py"

FAKE_SLOPSIFT = r'''#!/usr/bin/env python3
import json, os, sys
mode = os.environ.get("FAKE_MODE", "clean")
args = sys.argv[1:]
if args == ["--version"]:
    print("0.0.0-fake"); sys.exit(0)
log = os.environ.get("FAKE_LOG")
if log:
    open(log, "a").write("slopsift " + json.dumps(args) + "\n")
if mode == "fail":
    print("slopsift: model runtime failure", file=sys.stderr); sys.exit(2)
if mode == "garbage":
    print("not json"); sys.exit(0)
files = [a for a in args if a.endswith(".md") or a.endswith(".txt")]
out = []
for f in files:
    msgs = []
    if mode == "findings":
        msgs.append({"ruleId": "ai-style/promo-idioms", "ruleUrl": "https://slopsift.dev/rules/promo-idioms/",
                     "category": "promo", "severity": 1, "level": "warn", "confidence": "medium",
                     "start": 4, "end": 18, "text": "groundbreaking", "message": "Promotional tone.",
                     "line": 1, "column": 5, "endLine": 1, "endColumn": 19})
    out.append({"filePath": f, "rulesetVersion": "slopsift@0.0.0", "messages": msgs,
                "errorCount": 0, "warningCount": len(msgs), "infoCount": 0,
                "wordCount": 5, "findingsPerThousandWords": 0})
print(json.dumps(out))
'''

FAKE_VALE = r'''#!/usr/bin/env python3
import json, os, sys
mode = os.environ.get("FAKE_MODE", "clean")
args = sys.argv[1:]
if args == ["--version"]:
    print("vale version 0.0.0-fake"); sys.exit(0)
log = os.environ.get("FAKE_LOG")
if log:
    open(log, "a").write("vale " + json.dumps(args) + "\n")
has_config = any(a.startswith("--config=") for a in args)
if mode == "noconfig" and not has_config:
    print(json.dumps({"Line": 0, "Path": "", "Text": "no config file found", "Code": "E100", "Span": 0}), file=sys.stderr)
    sys.exit(2)
if mode == "fail":
    print(json.dumps({"Line": 0, "Path": "", "Text": "style 'Google' does not exist", "Code": "E201", "Span": 0}), file=sys.stderr)
    sys.exit(2)
files = [a for a in args if not a.startswith("--")]
out = {}
if mode in ("findings", "noconfig"):
    for f in files:
        out[f] = [{"Action": {"Name": "", "Params": None}, "Span": [6, 14], "Check": "Vale.Repetition",
                   "Description": "", "Link": "", "Message": "'very' is repeated!", "Severity": "error",
                   "Match": "very very", "Line": 1}]
print(json.dumps(out))
'''


def make_exe(directory, name, body):
    path = Path(directory) / name
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def make_pptx(path):
    """Write a two-slide .pptx with speaker notes on slide 1, using only the parts lint.py reads."""
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    p = "http://schemas.openxmlformats.org/presentationml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    notes_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
    slide_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"

    def shape(text, ph=None):
        phx = f'<p:nvSpPr><p:cNvPr id="1" name="s"/><p:cNvSpPr/><p:nvPr><p:ph type="{ph}"/></p:nvPr></p:nvSpPr>' if ph else ""
        return f'<p:sp>{phx}<p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'

    def slide(*texts):
        body = "".join(shape(t) for t in texts)
        return f'<p:sld xmlns:a="{a}" xmlns:p="{p}"><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>'

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/presentation.xml",
                   f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst>'
                   f'<p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId3"/></p:sldIdLst></p:presentation>')
        z.writestr("ppt/_rels/presentation.xml.rels",
                   f'<Relationships xmlns="{rel}">'
                   f'<Relationship Id="rId2" Type="{slide_type}" Target="slides/slide1.xml"/>'
                   f'<Relationship Id="rId3" Type="{slide_type}" Target="slides/slide2.xml"/></Relationships>')
        z.writestr("ppt/slides/slide1.xml", slide("Revenue grew 12% on renewals", "Source: Q3 ledger"))
        z.writestr("ppt/slides/slide2.xml", slide("Churn sits in month-two accounts"))
        z.writestr("ppt/slides/_rels/slide1.xml.rels",
                   f'<Relationships xmlns="{rel}"><Relationship Id="rId1" Type="{notes_type}" '
                   f'Target="../notesSlides/notesSlide1.xml"/></Relationships>')
        z.writestr("ppt/notesSlides/notesSlide1.xml",
                   f'<p:notes xmlns:a="{a}" xmlns:p="{p}"><p:cSld><p:spTree>'
                   + shape("1", "sldNum") + shape("Say the 12% figure, then the renewal count.", "body")
                   + '</p:spTree></p:cSld></p:notes>')


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.slopsift = make_exe(self.dir, "slopsift", FAKE_SLOPSIFT)
        self.vale = make_exe(self.dir, "vale", FAKE_VALE)
        self.draft = self.dir / "draft.md"
        self.draft.write_text("Our groundbreaking very very tool.\n", encoding="utf-8")
        self.log = self.dir / "calls.log"

    def tearDown(self):
        self.tmp.cleanup()

    def lint(self, *args, mode="clean", slopsift=None, vale=None):
        env = dict(os.environ)
        env.update(FAKE_MODE=mode, FAKE_LOG=str(self.log),
                   SLOPSIFT_BIN=str(slopsift or self.slopsift), VALE_BIN=str(vale or self.vale))
        p = subprocess.run([sys.executable, "-I", str(LINT), *args], capture_output=True,
                           text=True, env=env, cwd=self.dir)
        report = json.loads(p.stdout) if p.stdout.strip().startswith("{") else None
        return p.returncode, report, p

    def test_clean(self):
        code, r, _ = self.lint(str(self.draft))
        self.assertEqual(code, 0)
        self.assertEqual(r["status"], "clean")
        self.assertEqual([t["status"] for t in r["tools"]], ["ok", "ok"])
        self.assertEqual(r["findings"], [])

    def test_findings_are_normalized_and_keep_original(self):
        code, r, _ = self.lint(str(self.draft), mode="findings")
        self.assertEqual(code, 1)
        self.assertEqual(r["status"], "findings")
        self.assertEqual(len(r["findings"]), 2)
        for f in r["findings"]:
            for key in ("file", "location", "tool", "rule", "severity", "message", "original"):
                self.assertIn(key, f)
            self.assertEqual(f["file"], str(self.draft))
            self.assertIn(f["severity"], ("error", "warning", "info"))
        by_tool = {f["tool"]: f for f in r["findings"]}
        self.assertEqual(by_tool["slopsift"]["severity"], "warning")
        self.assertEqual(by_tool["slopsift"]["location"], {"line": 1, "column": 5, "end_line": 1, "end_column": 19})
        self.assertEqual(by_tool["slopsift"]["original"]["confidence"], "medium")
        self.assertEqual(by_tool["vale"]["rule"], "Vale.Repetition")
        self.assertEqual(by_tool["vale"]["original"]["Span"], [6, 14])

    def test_missing_tools_are_not_clean(self):
        code, r, _ = self.lint(str(self.draft), slopsift=self.dir / "nope", vale=self.dir / "nope")
        self.assertEqual(code, 2)
        self.assertEqual(r["status"], "incomplete")
        self.assertEqual([t["status"] for t in r["tools"]], ["missing", "missing"])
        self.assertTrue(all("does not install" in t["note"] for t in r["tools"]))

    def test_one_missing_tool_still_reports_the_other(self):
        code, r, _ = self.lint(str(self.draft), mode="findings", vale=self.dir / "nope")
        self.assertEqual(code, 2)
        self.assertEqual(r["status"], "incomplete")
        self.assertEqual({t["tool"]: t["status"] for t in r["tools"]}, {"slopsift": "ok", "vale": "missing"})
        self.assertEqual([f["tool"] for f in r["findings"]], ["slopsift"])

    def test_execution_failure_preserves_diagnostics(self):
        code, r, _ = self.lint(str(self.draft), mode="fail")
        self.assertEqual(code, 2)
        tools = {t["tool"]: t for t in r["tools"]}
        self.assertEqual(tools["slopsift"]["status"], "failed")
        self.assertEqual(tools["slopsift"]["exit_code"], 2)
        self.assertIn("model runtime failure", tools["slopsift"]["stderr"])
        self.assertEqual(tools["vale"]["status"], "failed")
        self.assertIn("E201", tools["vale"]["error"])
        self.assertEqual(r["findings"], [])

    def test_unreadable_output_is_a_failure(self):
        code, r, _ = self.lint(str(self.draft), "--tool", "slopsift", mode="garbage")
        self.assertEqual(code, 2)
        self.assertEqual(r["tools"][0]["status"], "failed")
        self.assertIn("unreadable JSON", r["tools"][0]["error"])

    def test_vale_without_project_config_uses_bundled_config(self):
        code, r, _ = self.lint(str(self.draft), "--tool", "vale", mode="noconfig")
        self.assertEqual(code, 1)
        self.assertEqual(r["tools"][0]["config"], "bundled")
        self.assertTrue(any("--config=" in a and a.endswith(".vale.ini") for a in r["tools"][0]["command"]))

    def test_slopsift_never_downloads(self):
        self.lint(str(self.draft), "--tool", "slopsift")
        calls = [json.loads(l.split(" ", 1)[1]) for l in self.log.read_text().splitlines() if l.startswith("slopsift")]
        self.assertTrue(calls)
        self.assertTrue(all("--no-download" in c for c in calls))

    def test_pptx_slides_and_notes_are_separate_documents(self):
        deck = self.dir / "deck.pptx"
        make_pptx(deck)
        code, r, _ = self.lint(str(deck), mode="findings")
        self.assertEqual(code, 1)
        self.assertEqual([(d["file"], d["part"]) for d in r["documents"]],
                         [(str(deck), "slides"), (str(deck), "notes")])
        parts = {(f["part"], f["tool"]) for f in r["findings"]}
        self.assertEqual(parts, {("slides", "slopsift"), ("slides", "vale"), ("notes", "slopsift"), ("notes", "vale")})
        self.assertTrue(all(f["location"].get("slide") == 1 for f in r["findings"]))

    def test_pptx_extraction_text(self):
        sys.path.insert(0, str(HERE))
        try:
            import lint
        finally:
            sys.path.pop(0)
        deck = self.dir / "deck.pptx"
        make_pptx(deck)
        out = self.dir / "out"
        out.mkdir()
        spath, smap, npath, nmap = lint.extract_pptx(deck, out)
        slides = spath.read_text().splitlines()
        notes = npath.read_text().splitlines()
        self.assertIn("Revenue grew 12% on renewals", slides)
        self.assertIn("Churn sits in month-two accounts", slides)
        self.assertEqual(smap[slides.index("Churn sits in month-two accounts") + 1], 2)
        self.assertEqual(notes, ["Say the 12% figure, then the renewal count."])
        self.assertEqual(nmap, {1: 1})

    def test_unsupported_input_is_a_usage_error(self):
        bad = self.dir / "page.pdf"
        bad.write_bytes(b"%PDF-1.4")
        code, r, p = self.lint(str(bad))
        self.assertEqual(code, 64)
        self.assertIsNone(r)
        self.assertIn("unsupported file type", p.stderr)

    def test_stdin(self):
        env = dict(os.environ, FAKE_MODE="findings", SLOPSIFT_BIN=str(self.slopsift), VALE_BIN=str(self.vale))
        p = subprocess.run([sys.executable, "-I", str(LINT), "-", "--format", "text"], input="Our groundbreaking tool.\n",
                           capture_output=True, text=True, env=env, cwd=self.dir)
        self.assertEqual(p.returncode, 1)
        self.assertIn("-:1:5 warning slopsift ai-style/promo-idioms", p.stdout)
        self.assertIn("not proof of AI authorship", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
