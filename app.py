import streamlit as st
import unicodedata
import random
import json
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz
from st_keyup import st_keyup
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="O Mestre do Português", page_icon="🇧🇷", layout="centered")

# --- CSS PERSONNALISÉ (SOBRE & COMPACT) ---
st.markdown("""
    <style>
        .main { background-color: #ffffff; }
        
        /* Champ de texte blanc */
        .stTextInput > div > div > input { 
            background-color: #ffffff; color: #1e1e1e; 
            border: 1px solid #d0d0d0; border-radius: 4px;
        }

        [data-testid="stExpander"] [data-testid="stHorizontalBlock"] {
            gap: 0.35rem !important;
        }

        [data-testid="stExpander"] [data-testid="column"] {
            padding: 0 !important;
        }

        [data-testid="stExpander"] button {
            width: 100% !important;
            min-width: 0 !important;
            min-height: 34px !important;
            height: auto !important;
            padding: 0.1rem !important;
            border-radius: 6px !important;
            font-size: 0.78rem !important;
            white-space: normal !important;
            line-height: 1.25 !important;
        }

        .quiz-progress {
            width: 100%;
            height: 12px;
            background: #d9d9d9;
            border-radius: 999px;
            overflow: hidden;
            margin: 0.35rem 0 1.25rem 0;
        }

        .quiz-progress-fill {
            height: 100%;
            background: #1f6fff;
            border-radius: 999px;
            transition: width 0.2s ease;
        }

        @media (max-width: 640px) {
            [data-testid="stForm"] {
                width: 100% !important;
                max-width: 100% !important;
                overflow-x: hidden !important;
            }

            [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                gap: 0.35rem !important;
                width: 100% !important;
                max-width: 100% !important;
            }

            [data-testid="stForm"] [data-testid="column"] {
                flex: 1 1 0 !important;
                width: 50% !important;
                max-width: 50% !important;
                min-width: 0 !important;
                padding: 0 !important;
            }

            [data-testid="stForm"] [data-testid="column"] > div {
                width: 100% !important;
                min-width: 0 !important;
            }

            [data-testid="stForm"] button {
                width: 100% !important;
                max-width: 100% !important;
                font-size: 0.72rem !important;
                padding-left: 0.25rem !important;
                padding-right: 0.25rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)



# --- CONNEXION BDD CLOUD (Google Sheets) ---
# Dans Streamlit Cloud, tu devras configurer l'URL dans les "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

VERBS_DATASET_PATH = Path("verbs_dataset.json")
OFFLINE_TEMPLATE_PATH = Path("offline_quiz_template.html")
SHEET_NAME = "Feuille1"


def normalize(text):
    text = str(text).lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace(" ", "").replace("...", "").replace("?", "")
    return text.strip()


def normalize_tokens(text):
    text = str(text).lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace("...", "").replace("?", "")
    return " ".join(text.split()).strip()


def answer_similarity(user_input, target):
    user = normalize_tokens(user_input)
    target = normalize_tokens(target)

    if not user:
        return 0

    score = fuzz.WRatio(user, target)

    if user in target or target in user:
        score = max(score, 95)

    return score


def sanitize_dir(value):
    try:
        int_value = int(value)
        if int_value in (0, 1):
            return int_value
    except (TypeError, ValueError):
        pass
    return random.randint(0, 1)


def sanitize_entry(entry):
    fr = str(entry.get("fr", "")).strip()
    pt = str(entry.get("pt", "")).strip()
    if not fr or not pt:
        return None
    source = str(entry.get("source", "vocab")).strip() or "vocab"
    return {"fr": fr, "pt": pt, "dir": sanitize_dir(entry.get("dir")), "source": source}


def deduplicate_entries(entries):
    unique_entries = []
    seen = set()

    for entry in entries:
        sanitized = sanitize_entry(entry)
        if not sanitized:
            continue

        key = (normalize_tokens(sanitized["fr"]), normalize_tokens(sanitized["pt"]))
        if key in seen:
            continue

        seen.add(key)
        unique_entries.append(sanitized)

    return unique_entries


def load_verbs_dataset():
    if not VERBS_DATASET_PATH.exists():
        return []

    with VERBS_DATASET_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return deduplicate_entries([{**item, "source": "conjugaison"} for item in data])


def read_sheet_entries():
    try:
        df = conn.read(worksheet=SHEET_NAME, ttl="10m")
    except Exception as e:
        st.warning(f"Connexion Google Sheets indisponible : {e}")
        return []

    if df is None or df.empty:
        return []

    return deduplicate_entries([{**item, "source": "vocab"} for item in df.to_dict("records")])


def load_base_db():
    verbs_entries = load_verbs_dataset()
    sheet_entries = read_sheet_entries()
    return deduplicate_entries([*verbs_entries, *sheet_entries])


def save_word_to_sheet(entry):
    try:
        current_df = conn.read(worksheet=SHEET_NAME)

        sheet_entry = {"fr": entry["fr"], "pt": entry["pt"], "dir": entry["dir"]}
        new_row_df = pd.DataFrame([sheet_entry])

        if current_df is None or current_df.empty:
            updated_df = new_row_df
        else:
            updated_df = pd.concat([current_df, new_row_df], ignore_index=True)

        conn.update(worksheet=SHEET_NAME, data=updated_df)

    except Exception as e:
        raise RuntimeError(f"Erreur écriture Google Sheets : {e}") from e


def verify_translation_pair(fr_word, pt_word):
    translator_fr_pt = GoogleTranslator(source="fr", target="pt")
    translator_pt_fr = GoogleTranslator(source="pt", target="fr")

    expected_pt = translator_fr_pt.translate(fr_word)
    expected_fr = translator_pt_fr.translate(pt_word)

    fr_score = answer_similarity(expected_fr, fr_word)
    pt_score = answer_similarity(expected_pt, pt_word)

    return {
        "ok": fr_score >= 100 or pt_score >= 100,
        "expected_pt": expected_pt,
        "expected_fr": expected_fr,
        "fr_score": fr_score,
        "pt_score": pt_score,
    }


def render_add_word_keyboard_shortcuts():
    components.html(
        """
        <script>
        const setup = () => {
          const doc = window.parent.document;
          const frInput = doc.querySelector('input[aria-label="Mot en Français"]');
          const ptInput = doc.querySelector('input[aria-label="Mot en Portugais"]');
          const submitButton = [...doc.querySelectorAll('button')].find(
            (button) => button.textContent && button.textContent.includes('Ajouter à la BDD')
          );

          if (!frInput || !ptInput || !submitButton) {
            window.setTimeout(setup, 250);
            return;
          }

          if (!frInput.dataset.enterShortcutBound) {
            frInput.addEventListener('keydown', (event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                ptInput.focus();
              }
            });
            frInput.dataset.enterShortcutBound = '1';
          }

          if (!ptInput.dataset.enterShortcutBound) {
            ptInput.addEventListener('keydown', (event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                submitButton.click();
              }
            });
            ptInput.dataset.enterShortcutBound = '1';
          }
        };

        setup();
        </script>
        """,
        height=0,
    )


def translate_sidebar_text():
    direction = st.session_state.get("translator_direction", "fr_to_pt")
    source_text = st.session_state.get("translator_source_text", "").strip()
    request_key = (direction, source_text)

    if not source_text:
        st.session_state.translator_target_text = ""
        st.session_state.translator_error = None
        st.session_state.translator_last_request = None
        return

    if st.session_state.get("translator_last_request") == request_key:
        return

    source_lang = "fr" if direction == "fr_to_pt" else "pt"
    target_lang = "pt" if direction == "fr_to_pt" else "fr"

    try:
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(source_text)
        st.session_state.translator_target_text = translated_text
        st.session_state.translator_error = None
        st.session_state.translator_last_request = request_key
    except Exception as exc:
        st.session_state.translator_target_text = ""
        st.session_state.translator_error = f"Traduction indisponible : {exc}"
        st.session_state.translator_last_request = None


def invert_sidebar_translation():
    current_source = st.session_state.get("translator_source_text", "")
    current_target = st.session_state.get("translator_target_text", "")

    st.session_state.translator_direction = (
        "pt_to_fr" if st.session_state.get("translator_direction", "fr_to_pt") == "fr_to_pt" else "fr_to_pt"
    )
    st.session_state.translator_source_text = current_target
    st.session_state.translator_target_text = current_source
    st.session_state.translator_error = None
    st.session_state.translator_last_request = None


def add_translator_pair_to_db():
    direction = st.session_state.get("translator_direction", "fr_to_pt")
    source_text = st.session_state.get("translator_source_text", "").strip()
    target_text = st.session_state.get("translator_target_text", "").strip()

    if not source_text or not target_text:
        st.session_state.admin_feedback = ("warning", "Aucune traduction complete à ajouter.")
        return

    if direction == "fr_to_pt":
        new_row = {
            "fr": source_text,
            "pt": target_text,
            "dir": random.randint(0, 1),
            "source": "vocab",
        }
    else:
        new_row = {
            "fr": target_text,
            "pt": source_text,
            "dir": random.randint(0, 1),
            "source": "vocab",
        }

    existing_pairs = {
        (normalize_tokens(item["fr"]), normalize_tokens(item["pt"]))
        for item in st.session_state.base_db
    }
    new_pair = (normalize_tokens(new_row["fr"]), normalize_tokens(new_row["pt"]))
    if new_pair in existing_pairs:
        st.session_state.admin_feedback = ("warning", "Cette traduction existe déjà dans la base.")
        return

    try:
        save_word_to_sheet(new_row)
        st.session_state.base_db = deduplicate_entries([*st.session_state.base_db, new_row])
        st.session_state.admin_feedback = (
            "success",
            f"**{new_row['fr']}** = **{new_row['pt']}** ajouté depuis le traducteur !",
        )
    except Exception as exc:
        st.session_state.admin_feedback = ("error", f"Impossible d'ajouter la traduction : {exc}")


def build_offline_quiz_html(quiz_entries):
    if not OFFLINE_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template introuvable : {OFFLINE_TEMPLATE_PATH}")

    quiz_payload = [
        {
            "fr": item["fr"],
            "pt": item["pt"],
            "dir": int(item["dir"]),
            "source": item.get("source", "vocab"),
        }
        for item in quiz_entries
    ]

    quiz_json = json.dumps(quiz_payload, ensure_ascii=False).replace("</", "<\\/")
    template = OFFLINE_TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template
        .replace("__QUIZ_DATA_JSON__", quiz_json)
        .replace("__QUIZ_TITLE__", "O Mestre do Portugues - Quiz hors ligne")
        .replace("__MANIFEST_LINK__", "")
        .replace("__PWA_BOOTSTRAP__", "")
    )


def render_offline_export_button():
    if not st.session_state.db:
        return

    offline_html = build_offline_quiz_html(st.session_state.db)
    st.download_button(
        "Télécharger le quiz hors ligne",
        data=offline_html,
        file_name="quiz_portugais_offline.html",
        mime="text/html",
        use_container_width=True,
        help="Télécharge une page HTML autonome du quiz courant. Elle fonctionne ensuite sans réseau.",
    )

if 'base_db' not in st.session_state:
    st.session_state.base_db = load_base_db()

if 'translator_direction' not in st.session_state:
    st.session_state.translator_direction = "fr_to_pt"
if 'translator_source_text' not in st.session_state:
    st.session_state.translator_source_text = ""
if 'translator_target_text' not in st.session_state:
    st.session_state.translator_target_text = ""
if 'translator_error' not in st.session_state:
    st.session_state.translator_error = None
if 'translator_last_request' not in st.session_state:
    st.session_state.translator_last_request = None

# --- SECTION ADMINISTRATION (Ajouter un mot) ---
with st.sidebar.expander("Ajouter du vocabulaire"):
    with st.container():
        admin_feedback = st.session_state.get("admin_feedback")
        with st.form("add_word_form", clear_on_submit=True):
            new_fr = st.text_input("Mot en Français", key="new_fr_input")
            new_pt = st.text_input("Mot en Portugais", key="new_pt_input")
            submit_new = st.form_submit_button("   Ajouter à la BDD   ")
            
            if submit_new and new_fr and new_pt:
                new_row = {"fr": new_fr.strip(), "pt": new_pt.strip(), "dir": random.randint(0, 1), "source": "vocab"}

                existing_pairs = {
                    (normalize_tokens(item["fr"]), normalize_tokens(item["pt"]))
                    for item in st.session_state.base_db
                }
                new_pair = (normalize_tokens(new_row["fr"]), normalize_tokens(new_row["pt"]))
                if new_pair in existing_pairs:
                    st.warning("Ce mot existe déjà dans la base chargée.")
                else:
                    try:
                        verification = verify_translation_pair(new_row["fr"], new_row["pt"])
                    except Exception as exc:
                        verification = None
                        st.warning(f"Vérification indisponible pour le moment : {exc}")

                    if verification and not verification["ok"]:
                        st.session_state.pending_word = new_row
                        st.session_state.pending_verification = verification
                    else:
                        try:
                            save_word_to_sheet(new_row)
                            st.session_state.base_db = deduplicate_entries([*st.session_state.base_db, new_row])
                            if verification:
                                st.session_state.admin_feedback = (
                                    "success",
                                    f"**{new_fr}** = **{new_pt}** ajouté !",
                                )
                            else:
                                st.session_state.admin_feedback = ("success", f"**{new_fr}** ajouté !")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Impossible d'ajouter le mot : {exc}")

        if admin_feedback:
            feedback_type, feedback_message = admin_feedback
            if feedback_type == "success":
                st.success(feedback_message)
            elif feedback_type == "warning":
                st.warning(feedback_message)
            else:
                st.error(feedback_message)
            st.session_state.admin_feedback = None

        render_add_word_keyboard_shortcuts()

        pending_word = st.session_state.get("pending_word")
        pending_verification = st.session_state.get("pending_verification")
        if pending_word and pending_verification:
            st.warning(
                "La traduction saisie semble incohérente. "
                f"**{pending_word['fr']}** ≠ **{pending_word['pt']}** selon la vérification automatique. "
                f"Suggestion : **{pending_word['pt']}** (PT) ≈ **{pending_verification['expected_fr']}** (FR)"
            )
            st.write("Es-tu sûr de cette traduction ?")
            confirm_col, cancel_col = st.columns([1, 1.8])
            if confirm_col.button("Oui", key="confirm_pending_word", use_container_width=True):
                try:
                    save_word_to_sheet(pending_word)
                    st.session_state.base_db = deduplicate_entries([*st.session_state.base_db, pending_word])
                    st.session_state.admin_feedback = (
                        "success",
                        f"**{pending_word['fr']}** = **{pending_word['pt']}** ajouté malgré l'avertissement.",
                    )
                except Exception as exc:
                    st.error(f"Impossible d'ajouter le mot : {exc}")
                finally:
                    st.session_state.pending_word = None
                    st.session_state.pending_verification = None
                st.rerun()
            if cancel_col.button("Non, ajouter la recommandation", key="cancel_pending_word", use_container_width=True):
                recommended_word = {
                    "fr": pending_verification["expected_fr"],
                    "pt": pending_word["pt"],
                    "dir": random.randint(0, 1),
                    "source": "vocab",
                }
                try:
                    save_word_to_sheet(recommended_word)
                    st.session_state.base_db = deduplicate_entries([*st.session_state.base_db, recommended_word])
                    st.session_state.admin_feedback = (
                        "success",
                        f"**{recommended_word['fr']}** = **{recommended_word['pt']}** ajouté malgré l'avertissement.",
                    )
                except Exception as exc:
                    st.error(f"Impossible d'ajouter la traduction recommandée : {exc}")
                finally:
                    st.session_state.pending_word = None
                    st.session_state.pending_verification = None
                st.rerun()

with st.sidebar.expander("Traduction FR/PT"):
    is_fr_to_pt = st.session_state.translator_direction == "fr_to_pt"
    source_label = "Français" if is_fr_to_pt else "Português"
    target_label = "Português" if is_fr_to_pt else "Français"

    st.button(
        "Inverser la traduction",
        key="translator_invert_button",
        on_click=invert_sidebar_translation,
        use_container_width=True,
    )
    previous_source_text = st.session_state.translator_source_text
    source_text = st_keyup(
        source_label,
        value=previous_source_text,
        key=f"translator_source_keyup_{st.session_state.translator_direction}",
        placeholder=f"Écris en {source_label.lower()}...",
    )
    st.session_state.translator_source_text = source_text or ""
    if st.session_state.translator_source_text != previous_source_text:
        st.session_state.translator_last_request = None
    translate_sidebar_text()
    st.text_input(
        target_label,
        key="translator_target_text",
        disabled=False,
    )
    st.button(
        "Ajouter cette traduction",
        key="translator_add_to_db",
        on_click=add_translator_pair_to_db,
        use_container_width=True,
    )

    if st.session_state.translator_error:
        st.warning(st.session_state.translator_error)

# --- SESSION STATE ---
if 'index' not in st.session_state:
    st.session_state.index = 0
    st.session_state.history = []
    st.session_state.last_feedback = None
    st.session_state.quiz_finished = False
    st.session_state.quiz_started = False
    st.session_state.selected_n = min(20, len(st.session_state.base_db))
    st.session_state.selected_conjugation_pct = 10
    st.session_state.db = []
    st.session_state.input_field = ""
    st.session_state.pending_word = None
    st.session_state.pending_verification = None
    st.session_state.admin_feedback = None

if 'admin_feedback' not in st.session_state:
    st.session_state.admin_feedback = None


def is_correct_answer(user_input, target):
    return answer_similarity(user_input, target) >= 85

def progress_class(status, idx, current_idx):
    classes = ["progress-box"]
    if status is True:
        classes.append("correct")
    elif status is False:
        classes.append("incorrect")
    if idx == current_idx:
        classes.append("current")
    return " ".join(classes)

def jump_to_question(idx):
    st.session_state.index = idx
    st.session_state.last_feedback = None
    if st.session_state.history.count(None) > 0:
        st.session_state.quiz_finished = False

def next_unanswered_index(current_idx, history):
    total = len(history)
    for idx in range(current_idx + 1, total):
        if history[idx] is None:
            return idx
    for idx in range(0, current_idx + 1):
        if history[idx] is None:
            return idx
    return total

def progress_label(status, idx, current_idx):
    if idx == current_idx:
        prefix = "▶"
    elif status is True:
        prefix = "🤙"
    elif status is False:
        prefix = "💩"
    else:
        prefix = "👀"
    return f"{prefix} {idx + 1}"

def build_quiz_sample(sample_size, conjugation_pct):
    conjugation_entries = [item for item in st.session_state.base_db if item.get("source") == "conjugaison"]
    vocab_entries = [item for item in st.session_state.base_db if item.get("source") != "conjugaison"]

    total_available = len(conjugation_entries) + len(vocab_entries)
    sample_size = min(sample_size, total_available)
    if sample_size <= 0:
        return []

    target_conjugation = round(sample_size * (conjugation_pct / 100))
    target_conjugation = min(target_conjugation, len(conjugation_entries))
    target_vocab = sample_size - target_conjugation

    if target_vocab > len(vocab_entries):
        missing_vocab = target_vocab - len(vocab_entries)
        target_vocab = len(vocab_entries)
        target_conjugation = min(len(conjugation_entries), target_conjugation + missing_vocab)

    if target_conjugation > len(conjugation_entries):
        missing_conjugation = target_conjugation - len(conjugation_entries)
        target_conjugation = len(conjugation_entries)
        target_vocab = min(len(vocab_entries), target_vocab + missing_conjugation)

    sampled_entries = []
    if target_conjugation > 0:
        sampled_entries.extend(random.sample(conjugation_entries, target_conjugation))
    if target_vocab > 0:
        sampled_entries.extend(random.sample(vocab_entries, target_vocab))

    random.shuffle(sampled_entries)
    return [item.copy() for item in sampled_entries]

def reset_quiz_state():
    st.session_state.index = 0
    st.session_state.history = [None] * len(st.session_state.db)
    st.session_state.last_feedback = None
    st.session_state.quiz_finished = False

def start_new_quiz(sample_size, conjugation_pct):
    st.session_state.selected_n = min(sample_size, len(st.session_state.base_db))
    st.session_state.selected_conjugation_pct = max(0, min(100, int(conjugation_pct)))
    st.session_state.db = build_quiz_sample(st.session_state.selected_n, st.session_state.selected_conjugation_pct)
    st.session_state.quiz_started = True
    reset_quiz_state()

def restart_inverted_quiz():
    st.session_state.db = [
        {
            "fr": item["fr"],
            "pt": item["pt"],
            "dir": 1 if item["dir"] == 0 else 0,
            "source": item.get("source", "vocab"),
        }
        for item in st.session_state.db
    ]
    st.session_state.quiz_started = True
    reset_quiz_state()

def return_to_setup():
    st.session_state.quiz_started = False
    st.session_state.db = []
    st.session_state.index = 0
    st.session_state.history = []
    st.session_state.last_feedback = None
    st.session_state.quiz_finished = False
    st.session_state.input_field = ""

def validate_current_answer(user_input=None):
    if st.session_state.quiz_finished or not st.session_state.db:
        return
    if st.session_state.index >= len(st.session_state.db):
        return
    if st.session_state.history[st.session_state.index] is not None:
        return

    q = st.session_state.db[st.session_state.index]
    target = q["pt"] if q["dir"] == 0 else q["fr"]
    if user_input is None:
        user_input = st.session_state.get("input_field", "")
    if is_correct_answer(user_input, target):
        st.session_state.history[st.session_state.index] = True
        st.session_state.last_feedback = ("success", f"**Correct !** {q['fr']} = **{q['pt']}**, tu as répondu : **{user_input}**")
    else:
        st.session_state.history[st.session_state.index] = False
        st.session_state.last_feedback = ("error", f"**Erreur !** La réponse était : **{target}**, tu as répondu : **{user_input}**")

    st.session_state.index = next_unanswered_index(st.session_state.index, st.session_state.history)
    if st.session_state.history.count(None) == 0:
        st.session_state.quiz_finished = True

def skip_current_question():
    if st.session_state.quiz_finished or not st.session_state.db:
        return
    if st.session_state.index >= len(st.session_state.db):
        return
    if st.session_state.history[st.session_state.index] is not None:
        return

    st.session_state.last_feedback = ("warning", "Question passée. Elle reste non repondue.")
    st.session_state.index += 1

def render_progress_bar(answered_count, total_count):
    percent = 0 if total_count == 0 else (answered_count / total_count) * 100
    st.markdown(
        (
            f'<div class="quiz-progress" title="{percent:.0f}% de progression">'
            f'<div class="quiz-progress-fill" style="width: {percent}%;"></div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


if not st.session_state.quiz_started:
    st.subheader("Paramètres du quiz")
    max_questions = len(st.session_state.base_db)
    selected_n = st.number_input(
        "Nombre de questions",
        min_value=1,
        max_value=max_questions,
        value=st.session_state.selected_n,
        step=1,
    )
    selected_conjugation_pct = st.number_input(
        "Pourcentage de conjugaison",
        min_value=0,
        max_value=100,
        value=st.session_state.selected_conjugation_pct,
        step=1,
    )
    if st.button("Commencer le quiz"):
        start_new_quiz(int(selected_n), int(selected_conjugation_pct))
        st.rerun()
    st.stop()

total_q = len(st.session_state.db)
score_total = sum(1 for x in st.session_state.history if x is True)
unanswered_count = st.session_state.history.count(None)
all_answered = unanswered_count == 0
answered_count = total_q - unanswered_count

# --- RÉCAPITULATIF COMPACT ---
st.sidebar.markdown("**État de progression**")
render_offline_export_button()
cols_per_row = 2
for row_start in range(0, total_q, cols_per_row):
    cols = st.sidebar.columns(cols_per_row)
    for offset, col in enumerate(cols):
        idx = row_start + offset
        if idx >= total_q:
            continue
        status = st.session_state.history[idx]
        button_type = "secondary"
        if idx == st.session_state.index:
            button_type = "primary"
        col.button(
            progress_label(status, idx, st.session_state.index),
            key=f"nav_{idx}",
            on_click=jump_to_question,
            args=(idx,),
            type=button_type,
            use_container_width=True,
        )

# --- QUIZ ---
if not st.session_state.quiz_finished and not all_answered:
    if st.session_state.index >= total_q:
        render_progress_bar(answered_count, total_q)
        header_col, score_col, button_col = st.columns([2, 2, 2], vertical_alignment="center")
        with header_col:
            st.write(" ")
        with score_col:
            st.write(f"**Score : {score_total} / {total_q}**")
        with button_col:
            if st.button("Terminer le quiz", key="finish_remaining"):
                st.session_state.quiz_finished = True
                st.rerun()
        st.header("Questions restantes")
        st.write(f"Il reste **{unanswered_count} questions** a completer.")
        st.info("Utilise le menu de progression pour revenir sur une question passée.")
        st.stop()

    q = st.session_state.db[st.session_state.index]
    prompt = q["fr"] if q["dir"] == 0 else q["pt"]
    target = q["pt"] if q["dir"] == 0 else q["fr"]
    label = "Français ➔ Portugais" if q["dir"] == 0 else "Português ➔ Francês"

    render_progress_bar(answered_count, total_q)
    header_col, score_col, button_col = st.columns([2, 2, 2], vertical_alignment="center")
    with header_col:
        st.write(f"Question {st.session_state.index + 1}")
    with score_col:
        st.write(f"**Score : {score_total} / {total_q}**")
    with button_col:
        if st.button("Terminer le quiz", key="finish_quiz"):
            st.session_state.quiz_finished = True
            st.rerun()

    st.subheader(prompt.upper())
    st.caption(label)

    # Vérifier si déjà répondu
    already_done = st.session_state.history[st.session_state.index] is not None

    if not already_done:
        with st.form(key="quiz_form", clear_on_submit=True, enter_to_submit=True):
            user_input = st.text_input("Ta réponse :", key="input_field")

            col1, col2 = st.columns(2)

            with col1:
                submit = st.form_submit_button("VALIDER", use_container_width=True)

            with col2:
                skip = st.form_submit_button("PASSER", use_container_width=True)

        if submit:
            validate_current_answer(user_input)
            st.rerun()

        if skip:
            skip_current_question()
            st.rerun()

        if st.session_state.last_feedback:
            f_type, f_msg = st.session_state.last_feedback
            if f_type == "success":
                st.success(f_msg)
            elif f_type == "warning":
                st.warning(f_msg)
            else:
                st.error(f_msg)

    else:

        # Question déjà répondue : on affiche juste la correction
        status_text = " Tu as eu juste !" if st.session_state.history[st.session_state.index] else " Tu as eu faux."
        color = "green" if st.session_state.history[st.session_state.index] else "red"

        st.markdown(
            f"<div style='color:{color}; font-weight:bold; font-size:20px;'>{status_text}</div>",
            unsafe_allow_html=True
        )

        st.write(f"Rappel de la traduction : **{q['fr']}** = **{q['pt']}**")

        if st.button("Question suivante ➡️"):
            st.session_state.index = next_unanswered_index(st.session_state.index, st.session_state.history)
            st.session_state.last_feedback = None
            if st.session_state.index >= total_q and st.session_state.history.count(None) == 0:
                st.session_state.quiz_finished = True
            st.rerun()

        if st.session_state.last_feedback:
            f_type, f_msg = st.session_state.last_feedback
            if f_type == "success":
                st.success(f_msg)
            elif f_type == "warning":
                st.warning(f_msg)
            else:
                st.error(f_msg)

else:
    # FIN DU QUIZ
    if st.session_state.last_feedback:
        f_type, f_msg = st.session_state.last_feedback
        if f_type == "success":
            st.success(f_msg)
        elif f_type == "warning":
            st.warning(f_msg)
        else:
            st.error(f_msg)
    render_progress_bar(answered_count, total_q)
    st.balloons()
    st.header("Fim do quiz ! 🎉")
    st.write(f"Score final : **{score_total} / {total_q}**")
    
    if unanswered_count > 0:
        st.warning(f"Il restait **{unanswered_count} questions** non repondues.")
    
    col1, col2 = st.columns(2)
    if col1.button("Inverser le sens de traduction"):
        restart_inverted_quiz()
        st.rerun()
    if col2.button("Nouveau quiz aléatoire"):
        return_to_setup()
        st.rerun()
