


def _load_local_secrets() -> None:
    """Fill the environment from ~/.config/paradise_garage/secrets.env.

    Low-value automation keys (Spotify developer app, Discogs token) live
    there in plain text, mode 0600, so `pg` runs without a 1Password prompt.
    The 1Password references stay in op.env next to it. Variables already set
    in the environment win.
    """
    import os
    from pathlib import Path

    path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "paradise_garage" / "secrets.env"
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_local_secrets()
