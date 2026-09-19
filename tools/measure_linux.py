import io
import json
import platform
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from bg_dvorak_phonetic.diagnostics import Diagnostics, InstallerError
from bg_dvorak_phonetic.platforms.linux import LinuxAdapter, symbol_spans
from bg_dvorak_phonetic.workflow import execute, project_root

root = project_root()
records = []
transcripts = []
with tempfile.TemporaryDirectory(prefix="bg-native-validation-") as name:
    temporary = Path(name)
    checkout = temporary / "checkout проект"
    checkout.mkdir()
    for directory in ("linux", "mac-os"):
        shutil.copytree(root / directory, checkout / directory)
    xkb = temporary / "xkb"
    (xkb / "symbols").mkdir(parents=True)
    (xkb / "rules").mkdir()
    for relative in ("symbols/bg", "rules/evdev.xml", "rules/base.xml"):
        shutil.copy2(Path("/usr/share/X11/xkb") / relative, xkb / relative)
    # Host distro files may contain a prior manual installation. Seed an explicitly
    # absent fixture before recording fresh-install behavior; never edit host files.
    symbols_path = xkb / "symbols/bg"
    data = symbols_path.read_bytes()
    for start, end in reversed(symbol_spans(data)):
        data = data[:start] + data[end:]
    symbols_path.write_bytes(data)
    for registry_path in (xkb / "rules/evdev.xml", xkb / "rules/base.xml"):
        document = ET.fromstring(registry_path.read_bytes())
        for layout in document.findall("./layoutList/layout"):
            if layout.findtext("configItem/name") == "bg":
                variants = layout.find("variantList")
                for variant in list(variants):
                    if variant.findtext("configItem/name") == "bg-dvorak-phonetic":
                        variants.remove(variant)
        registry_path.write_bytes(ET.tostring(document, encoding="utf-8"))
    clean_registry = (xkb / "rules/evdev.xml").read_bytes()
    adapter = LinuxAdapter(
        root=checkout, xkb_root=xkb, state_root=temporary / "state", testing=True
    )
    context = replace(adapter.probe("system"), scope="user")
    adapter.context = context

    def run(scenario, expected="unchanged"):
        stream = io.StringIO()
        start = time.perf_counter()
        result = execute(adapter, context, yes=True, diagnostics=Diagnostics(stream=stream))
        elapsed = time.perf_counter() - start
        assert result.action == expected, (scenario, result.action, expected)
        records.append({"scenario": scenario, "action": result.action, "seconds": elapsed})
        transcripts.append(
            f"### {scenario}\n\n```text\n"
            + stream.getvalue().replace(name, "<fixture>")
            + f"action={result.action} activation={result.activation_status}\n```\n"
        )

    run("fresh install", "installed")
    for i in range(3):
        run(f"current invocation {i + 1}")
    symbols = xkb / "symbols/bg"
    symbols.write_bytes(
        symbols.read_bytes().replace(b"Bulgarian (Dvorak phonetic)", b"Legacy project label")
    )
    run("legacy update", "updated")
    (xkb / "rules/evdev.xml").write_bytes(clean_registry)
    run("missing registration repair", "repaired")
    broken = xkb / "rules/evdev.xml"
    broken.write_bytes(b"<broken>")
    stream = io.StringIO()
    events = Diagnostics(stream=stream)
    try:
        execute(adapter, context, yes=True, diagnostics=events)
    except InstallerError as error:
        assert error.code == 4 and broken.read_bytes() == b"<broken>"
        events.error(error)
        transcripts.append(
            "### Unsafe XML refusal\n\n```text\n"
            + stream.getvalue().replace(name, "<fixture>")
            + "exit=4\n```\n"
        )
    else:
        raise AssertionError("Expected refusal")
validation = root / "specs/001-automate-layout-install/validation"
validation.mkdir(exist_ok=True)
(validation / "us3.md").write_text(
    "# Diagnostic validation\n\nNative Ubuntu 24.04 x86_64 fixture runs with CPython "
    + platform.python_version()
    + ". Destinations are temporary copies of distro XKB data; user ownership\n"
    + "is injected for these fixtures only. Production Linux requires system scope.\n"
    + "Actual xkbcli compile-keymap validates candidates\n"
    + "and installed fixture files. No live keyboard settings were changed.\n"
    + "Paths are sanitized.\n\n"
    + "\n".join(transcripts),
    encoding="utf-8",
)
(validation / "performance.md").write_text(
    "# Performance evidence\n\nUbuntu 24.04 x86_64, CPython "
    + platform.python_version()
    + ", actual native XKB compilation against temporary distro copies.\n"
    + "These timings include filesystem/journal/native validation but exclude setup,\n"
    + "authorization,\n"
    + "and desktop activation. They are local observations, not macOS or hosted-run results.\n\n"
    + "| Scenario | Result | Seconds |\n|---|---|---:|\n"
    + "\n".join(f"| {r['scenario']} | {r['action']} | {r['seconds']:.4f} |" for r in records)
    + "\n\nLocal runs meet the 5-second inspection/no-op and 30-second apply budgets.\n"
    + "macOS baseline measurements remain pending; T058 remains open.\n",
    encoding="utf-8",
)
print(json.dumps(records, indent=2))
