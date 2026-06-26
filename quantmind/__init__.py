"""QuantMind v2 package root.

Loads the project ``.env`` into ``os.environ`` at import time so every consumer —
pydantic ``Settings`` *and* the LLM clients (which read provider keys straight from
``os.environ``) — sees the keys regardless of entry point. ``override=False`` so a
value exported in the real environment always wins over the ``.env`` file;
``find_dotenv(usecwd=True)`` walks up from the CWD to find the project's ``.env``.
"""
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True), override=False)
except ImportError:  # python-dotenv is a dependency, but degrade gracefully
    pass
