import json
import random
import unicodedata
from pathlib import Path

from deep_translator import GoogleTranslator
from wordfreq import top_n_list


VOCAB_PATH = Path("vocabulary.json")
M = 100


def normalize(text):
    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(text.split())


def load_vocabulary():
    return json.loads(VOCAB_PATH.read_text(encoding="utf-8"))


def save_vocabulary(vocabulary):
    VOCAB_PATH.write_text(
        json.dumps(vocabulary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def existing_french_entries(vocabulary):
    return {normalize(item["fr"]) for item in vocabulary}


def collect_new_words(count, existing_words):
    new_words = []
    seen = set(existing_words)
    scan_size = max(500, count * 20)

    while len(new_words) < count:
        candidates = top_n_list("fr", scan_size)
        for word in candidates:
            normalized = normalize(word)
            if not normalized or normalized in seen:
                continue
            if " " in normalized or "-" in normalized:
                continue
            if not normalized.isalpha():
                continue
            seen.add(normalized)
            new_words.append(word)
            if len(new_words) == count:
                return new_words
        scan_size *= 2

    return new_words


def build_entries(words):
    translator = GoogleTranslator(source="fr", target="pt")
    translations = translator.translate_batch(words)
    return [
        {"fr": fr_word, "pt": pt_word, "dir": random.randint(0, 1)}
        for fr_word, pt_word in zip(words, translations)
    ]


def main():

    vocabulary = load_vocabulary()
    existing_words = existing_french_entries(vocabulary)
    new_words = collect_new_words(M, existing_words)
    new_entries = build_entries(new_words)

    vocabulary.extend(new_entries)
    save_vocabulary(vocabulary)

    print(f"{len(new_entries)} nouveaux mots ajoutés a {VOCAB_PATH}")


if __name__ == "__main__":
    main()
