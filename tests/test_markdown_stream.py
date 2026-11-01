"""Markdown streaming helpers and code extraction."""
from hex_cli.tui.markdown_util import (
    balance_fences_for_preview,
    extract_code_blocks,
    last_code_block,
    is_near_bottom,
)


def test_balance_incomplete_fence():
    partial = "Here:\n```python\nprint(1)\n"
    fixed = balance_fences_for_preview(partial)
    assert fixed.rstrip().endswith("```")
    assert "print(1)" in fixed


def test_balance_complete_unchanged():
    full = "```js\nconst x=1;\n```\n"
    assert balance_fences_for_preview(full) == full


def test_extract_code_blocks():
    md = "Intro\n```python\ndef f():\n    return 1\n```\nOut\n```bash\necho hi\n```\n"
    blocks = extract_code_blocks(md)
    assert len(blocks) == 2
    assert blocks[0][0] == "python"
    assert "def f()" in blocks[0][1]
    assert blocks[0][1].startswith("def")
    assert last_code_block(md)[0] == "bash"
    assert "echo hi" in last_code_block(md)[1]


def test_unicode_code():
    md = "```text\nহ্যালো 🚀\n```\n"
    lang, code = extract_code_blocks(md)[0]
    assert "হ্যালো" in code
    assert "🚀" in code


def test_is_near_bottom():
    assert is_near_bottom(10, 12) is True
    assert is_near_bottom(0, 50) is False


def test_empty_and_odd_chunks():
    assert balance_fences_for_preview("") == ""
    assert extract_code_blocks("") == []
    assert last_code_block("no fences") is None


def test_large_response_extract():
    body = "\n".join(f"line {i}" for i in range(500))
    md = f"```python\n{body}\n```\n"
    blocks = extract_code_blocks(md)
    assert len(blocks) == 1
    assert blocks[0][1].count("\n") >= 499
