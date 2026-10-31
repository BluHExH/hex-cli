"""Provider registry and picker data tests."""
from hex_cli.providers.registry import list_provider_specs, get_provider_spec


def test_list_providers_nonempty():
    specs = list_provider_specs()
    assert len(specs) >= 5
    ids = {s.id for s in specs}
    assert "openrouter" in ids or "ollama" in ids


def test_ollama_no_key_required():
    s = get_provider_spec("ollama")
    assert s is not None
    assert s.requires_key is False


def test_provider_display_names():
    for s in list_provider_specs():
        assert s.display_name
        assert s.id
