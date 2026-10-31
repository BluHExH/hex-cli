"""Offline identity knowledge tests."""
from hex_cli.knowledge.identity import try_offline_identity, COMPANY, TAGLINE, PRODUCT_NAME


def test_who_are_you():
    r = try_offline_identity("Who are you?")
    assert r and PRODUCT_NAME in r


def test_who_built_you():
    r = try_offline_identity("Who built you?")
    assert r and COMPANY in r


def test_powers():
    r = try_offline_identity("What powers you?")
    assert r and "HEX" in r


def test_offline():
    r = try_offline_identity("Can you work offline?")
    assert r and "offline" in r.lower()


def test_coding_not_hijacked():
    assert try_offline_identity("Write a function to sort a list") is None
    assert try_offline_identity("Fix the bug in main.py") is None


def test_empty():
    assert try_offline_identity("") is None
    assert try_offline_identity("   ") is None
