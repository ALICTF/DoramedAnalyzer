import os

from core.settings import load_env_file


def test_load_env_file_sets_missing_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# local secrets",
                "GAPGPT_API_KEY=test-key",
                "DSTAND_LOG_LEVEL=DEBUG",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("GAPGPT_API_KEY", raising=False)
    monkeypatch.setenv("DSTAND_LOG_LEVEL", "INFO")

    load_env_file(str(env_file))

    assert os.environ["GAPGPT_API_KEY"] == "test-key"
    assert os.environ["DSTAND_LOG_LEVEL"] == "INFO"
