import streamlit as st
import unicodedata
import random
import json

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
            height: 34px !important;
            padding: 0.1rem !important;
            border-radius: 6px !important;
            font-size: 0.78rem !important;
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
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES (100 QUESTIONS) ---
if 'base_db' not in st.session_state:
    st.session_state.base_db = []
    with open("vocabulary.json", encoding="utf-8") as f:
        st.session_state.base_db.extend(json.load(f))
    with open("verbs_dataset.json", encoding="utf-8") as f:
        st.session_state.base_db.extend(json.load(f))
    
# --- SESSION STATE ---
if 'index' not in st.session_state:
    st.session_state.index = 0
    st.session_state.history = []
    st.session_state.last_feedback = None
    st.session_state.quiz_finished = False
    st.session_state.quiz_started = False
    st.session_state.selected_n = min(20, len(st.session_state.base_db))
    st.session_state.db = []

# --- LOGIQUE ---
def normalize(text):
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace(" ", "").replace("...", "").replace("?", "")
    return text.strip()

def levenshtein(s1, s2):
    s1, s2 = normalize(s1), normalize(s2)
    if len(s1) < len(s2): return levenshtein(s2, s1)
    if len(s2) == 0: return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(prev_row[j+1]+1, curr_row[j]+1, prev_row[j]+(c1!=c2)))
        prev_row = curr_row
    return prev_row[-1]

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

def build_quiz_sample(sample_size):
    sample_size = min(sample_size, len(st.session_state.base_db))
    return [item.copy() for item in random.sample(st.session_state.base_db, sample_size)]

def reset_quiz_state():
    st.session_state.index = 0
    st.session_state.history = [None] * len(st.session_state.db)
    st.session_state.last_feedback = None
    st.session_state.quiz_finished = False

def start_new_quiz(sample_size):
    st.session_state.selected_n = min(sample_size, len(st.session_state.base_db))
    st.session_state.db = build_quiz_sample(st.session_state.selected_n)
    st.session_state.quiz_started = True
    reset_quiz_state()

def restart_inverted_quiz():
    st.session_state.db = [
        {"fr": item["fr"], "pt": item["pt"], "dir": 1 if item["dir"] == 0 else 0}
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

def render_progress_bar(answered_count, total_count):
    percent = 0 if total_count == 0 else (answered_count / total_count) * 100
    st.markdown(
        (
            '<div class="quiz-progress">'
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
    if st.button("Commencer le quiz"):
        start_new_quiz(int(selected_n))
        st.rerun()
    st.stop()

total_q = len(st.session_state.db)
score_total = sum(1 for x in st.session_state.history if x is True)
unanswered_count = st.session_state.history.count(None)
all_answered = unanswered_count == 0
answered_count = total_q - unanswered_count

# --- RÉCAPITULATIF COMPACT ---
st.sidebar.markdown("**État de progression**")
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

        with st.form(key='quiz_form', clear_on_submit=True):

            user_input = st.text_input("Ta réponse :", key="input_field")

            col1, col2 = st.columns(2)

            with col1:
                skip = st.form_submit_button("PASSER", use_container_width=True)

            with col2:
                submit = st.form_submit_button("VALIDER", use_container_width=True)

        if submit:

            dist = levenshtein(user_input, target)

            if dist <= 1:
                st.session_state.history[st.session_state.index] = True
                st.session_state.last_feedback = ("success", f"**Correct !** {q['fr']} = **{q['pt']}**")

            else:
                st.session_state.history[st.session_state.index] = False
                st.session_state.last_feedback = ("error", f"**Erreur !** La réponse était : **{target}**")

            st.session_state.index = next_unanswered_index(st.session_state.index, st.session_state.history)
            if st.session_state.history.count(None) == 0:
                st.session_state.quiz_finished = True
            st.rerun()

        if skip:
            st.session_state.last_feedback = ("warning", "Question passée. Elle reste non repondue.")

            st.session_state.index += 1
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
        status_text = "✅ Tu as eu juste !" if st.session_state.history[st.session_state.index] else "❌ Tu as eu faux."
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
