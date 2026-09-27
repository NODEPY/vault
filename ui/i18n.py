import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=5)
def load_language(language):
    if language not in ("uk", "en", "pl", "de", "es"):
        language = "en"
    return json.loads((Path(__file__).parent / "locales" / f"{language}.json").read_text(encoding="utf-8"))


def translate(key, language="en", **values):
    return load_language(language)[key].format(**values)
