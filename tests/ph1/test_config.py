import pytest

from cl_st1.common.config import get_settings


def test_get_settings_raises_when_missing_env_vars(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

    with pytest.raises(RuntimeError) as exc:
        get_settings(env_file=None)

    msg = str(exc.value)
    assert "REDDIT_CLIENT_ID" in msg
    assert "REDDIT_CLIENT_SECRET" in msg