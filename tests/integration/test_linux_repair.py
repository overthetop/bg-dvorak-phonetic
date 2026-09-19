import pytest

from bg_dvorak_phonetic.diagnostics import InstallerError
from bg_dvorak_phonetic.platforms.linux import transform_registry, transform_symbols

REGISTRY = (
    b"<xkbConfigRegistry><layoutList><layout><configItem><name>bg</name></configItem>"
    b"<variantList>{}</variantList></layout>"
    b"<layout><configItem><name>other</name></configItem>"
    b"<variantList>{}</variantList></layout>"
    b"</layoutList></xkbConfigRegistry>"
)


def test_duplicate_owned_definitions_preserve_unrelated(project_root):
    source = (project_root / "linux/symbols-bg-dv").read_bytes().strip()
    other = b'// unrelated }\nxkb_symbols "similar-bg-dvorak-phonetic" { name[Group1]="{ }"; };\n'
    result = transform_symbols(other + source + b"\n" + source, source)
    assert result.startswith(other)
    assert result.count(b'xkb_symbols "bg-dvorak-phonetic"') == 1
    assert transform_symbols(result, source) == result


def test_xml_duplicates_match_only_bg(project_root):
    entry = (project_root / "linux/evdev.xml").read_bytes().strip()
    data = REGISTRY.replace(b"{}", entry + entry, 1).replace(b"{}", entry, 1)
    result = transform_registry(data, entry)
    assert result.count(b"<name>bg-dvorak-phonetic</name>") == 2
    assert (
        result[result.index(b"<layout><configItem><name>other") :]
        == data[data.index(b"<layout><configItem><name>other") :]
    )
    assert transform_registry(result, entry) == result


@pytest.mark.parametrize(
    "broken", [b'xkb_symbols "x" {', b"}", b"/* unterminated", b'"unterminated']
)
def test_unbounded_shared_symbols_refused(project_root, broken):
    with pytest.raises(InstallerError):
        transform_symbols(broken, (project_root / "linux/symbols-bg-dv").read_bytes())


def test_malformed_registry_refused(project_root):
    with pytest.raises(InstallerError):
        transform_registry(b"<broken>", (project_root / "linux/evdev.xml").read_bytes())
