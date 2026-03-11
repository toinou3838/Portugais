import streamlit as st
import unicodedata

# --- CONFIGURATION ---
st.set_page_config(page_title="O Mestre do Português", page_icon="🇧🇷", layout="centered")

# --- STYLE SOBRE ET DISCRET ---
st.markdown("""
    <style>
    /* Fond de page blanc */
    .main { background-color: #ffffff; }
    
    /* Champ de texte blanc avec bordure fine */
    .stTextInput > div > div > input { 
        background-color: #ffffff; 
        color: #1e1e1e; 
        border: 1px solid #e0e0e0; 
        border-radius: 5px;
        font-size: 18px;
    }
    
    /* Boutons uniformes */
    .stButton > button { 
        width: 100%; 
        border-radius: 5px; 
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        color: #444444;
    }
    
    /* Hover sur boutons */
    .stButton > button:hover {
        border-color: #4a90e2;
        color: #4a90e2;
    }

    /* Style pour la grille de progression */
    .dot-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        justify-content: center;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES (100 QUESTIONS) ---
if 'db' not in st.session_state:
    st.session_state.db = [
        {"fr": "prendre un taxi", "pt": "pegar um táxi", "dir": 0},
        {"fr": "ça va / tout va bien", "pt": "tudo bem", "dir": 1},
        {"fr": "tout le livre", "pt": "todo o livro", "dir": 0},
        {"fr": "est-ce possible de ... ?", "pt": "dá para ... ?", "dir": 1},
        {"fr": "un coup de main", "pt": "dar uma mão", "dir": 0},
        {"fr": "faire une cagnotte", "pt": "fazer vaquinha", "dir": 1},
        {"fr": "au cas où", "pt": "caso", "dir": 0},
        {"fr": "prendre soin de / veiller sur", "pt": "zelar", "dir": 1},
        {"fr": "avec qui", "pt": "com quem", "dir": 0},
        {"fr": "bouteille", "pt": "garrafa", "dir": 1},
        {"fr": "pour l'instant", "pt": "por enquanto", "dir": 0},
        {"fr": "néanmoins", "pt": "no entanto", "dir": 1},
        {"fr": "être contrarié", "pt": "ficar chateado", "dir": 0},
        {"fr": "être déçu", "pt": "ficar a ver navios", "dir": 1},
        {"fr": "en fait / à vrai dire", "pt": "na verdade", "dir": 0},
        {"fr": "oreille", "pt": "orelha", "dir": 1},
        {"fr": "bras", "pt": "braços", "dir": 0},
        {"fr": "de plus", "pt": "aliás", "dir": 1},
        {"fr": "dès que", "pt": "assim que", "dir": 0},
        {"fr": "genre / comme", "pt": "tipo", "dir": 1},
        {"fr": "c'est-à-dire", "pt": "quer dizer", "dir": 0},
        {"fr": "surtout", "pt": "sobretudo", "dir": 1},
        {"fr": "très", "pt": "muito", "dir": 0},
        {"fr": "beaucoup de", "pt": "muitos", "dir": 1},
        {"fr": "être tranquille", "pt": "ficar de boa", "dir": 0},
        {"fr": "à cause de", "pt": "por causa de", "dir": 1},
        {"fr": "les lèvres", "pt": "beiços", "dir": 0},
        {"fr": "cependant", "pt": "todavia", "dir": 1},
        {"fr": "épaule", "pt": "ombro", "dir": 0},
        {"fr": "trottoir", "pt": "calçada", "dir": 1},
        {"fr": "balai", "pt": "vassoura", "dir": 0},
        {"fr": "miroir", "pt": "espelho", "dir": 1},
        {"fr": "genou", "pt": "joelho", "dir": 0},
        {"fr": "immeuble", "pt": "prédio", "dir": 1},
        {"fr": "poubelle", "pt": "lixeira", "dir": 0},
        {"fr": "déchets", "pt": "lixo", "dir": 1},
        {"fr": "couteau", "pt": "faca", "dir": 0},
        {"fr": "assiette", "pt": "prato", "dir": 1},
        {"fr": "fourchette", "pt": "garfo", "dir": 0},
        {"fr": "cou", "pt": "pescoço", "dir": 1},
        {"fr": "mairie", "pt": "prefeitura", "dir": 0},
        {"fr": "coude", "pt": "cotovelo", "dir": 1},
        {"fr": "ongle", "pt": "unha", "dir": 0},
        {"fr": "boucherie", "pt": "açougue", "dir": 1},
        {"fr": "vide", "pt": "vazio", "dir": 0},
        {"fr": "jupe", "pt": "saia", "dir": 1},
        {"fr": "gare routière", "pt": "rodoviária", "dir": 0},
        {"fr": "évier", "pt": "pia", "dir": 1},
        {"fr": "bracelet", "pt": "pulseira", "dir": 0},
        {"fr": "sable", "pt": "areia", "dir": 1},
        {"fr": "chaud", "pt": "quente", "dir": 0},
        {"fr": "boucle d'oreille", "pt": "brinco", "dir": 1},
        {"fr": "gant", "pt": "luva", "dir": 0},
        {"fr": "arbre", "pt": "árvore", "dir": 1},
        {"fr": "cheville", "pt": "tornozelo", "dir": 0},
        {"fr": "poignet", "pt": "pulso", "dir": 1},
        {"fr": "poitrine / torse", "pt": "peito", "dir": 0},
        {"fr": "brosse", "pt": "escova", "dir": 1},
        {"fr": "impatient", "pt": "ansioso", "dir": 0},
        {"fr": "léger", "pt": "leve", "dir": 1},
        {"fr": "amer", "pt": "amargo", "dir": 0},
        {"fr": "fauché", "pt": "duro", "dir": 1},
        {"fr": "sale", "pt": "sujo", "dir": 0},
        {"fr": "garage", "pt": "oficina", "dir": 1},
        {"fr": "jaloux", "pt": "ciumento", "dir": 0},
        {"fr": "muet", "pt": "mudo", "dir": 1},
        {"fr": "où est... ?", "pt": "cadê", "dir": 0},
        {"fr": "boulangerie", "pt": "padaria", "dir": 1},
        {"fr": "pharmacie", "pt": "farmácia", "dir": 0},
        {"fr": "coin de rue", "pt": "esquina", "dir": 1},
        {"fr": "passage piéton", "pt": "faixa de pedestre", "dir": 0},
        {"fr": "feu rouge", "pt": "semáforo", "dir": 1},
        {"fr": "couloir", "pt": "corredor", "dir": 0},
        {"fr": "ascenseur", "pt": "elevador", "dir": 1},
        {"fr": "poignée de porte", "pt": "maçaneta", "dir": 0},
        {"fr": "tiroir", "pt": "gaveta", "dir": 1},
        {"fr": "oreiller", "pt": "travesseiro", "dir": 0},
        {"fr": "drap", "pt": "lençol", "dir": 1},
        {"fr": "voisinage", "pt": "vizinhança", "dir": 0},
        {"fr": "habiter", "pt": "morar", "dir": 1},
        {"fr": "en retard", "pt": "atrasado", "dir": 0},
        {"fr": "tôt", "pt": "cedo", "dir": 1},
        {"fr": "tard", "pt": "tarde", "dir": 0},
        {"fr": "certainement", "pt": "com certeza", "dir": 1},
        {"fr": "peut-être", "pt": "talvez", "dir": 0},
        {"fr": "avec moi", "pt": "comigo", "dir": 1},
        {"fr": "avec toi", "pt": "contigo", "dir": 0},
        {"fr": "louer", "pt": "alugar", "dir": 1},
        {"fr": "facture", "pt": "boleto", "dir": 0},
        {"fr": "snack-bar", "pt": "lanchonete", "dir": 1},
        {"fr": "primeur", "pt": "quitanda", "dir": 0},
        {"fr": "bureau", "pt": "escritório", "dir": 1},
        {"fr": "stage", "pt": "estágio", "dir": 0},
        {"fr": "conférence", "pt": "palestra", "dir": 1},
        {"fr": "fatigué", "pt": "cansado", "dir": 0},
        {"fr": "clé", "pt": "chave", "dir": 1},
        {"fr": "portefeuille", "pt": "carteira", "dir": 0},
        {"fr": "pièce de monnaie", "pt": "moeda", "dir": 1},
        {"fr": "addition", "pt": "conta", "dir": 0},
        {"fr": "pourboire", "pt": "gorjeta", "dir": 1}
    ]

# --- SESSION STATE ---
if 'index' not in st.session_state:
    st.session_state.index = 0
    st.session_state.history = [None] * len(st.session_state.db)
    st.session_state.last_feedback = None

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

# --- UI ---
st.title("🇧🇷 O Mestre do Português")

# --- RÉCAPITULATIF PLIABLE ---
with st.expander("📊 Voir mon récapitulatif (Progression)", expanded=False):
    cols_per_row = 10
    total_q = len(st.session_state.db)
    for i in range(0, total_q, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < total_q:
                status = st.session_state.history[idx]
                if status is True: color = "🟢"
                elif status is False: color = "🔴"
                else: color = "⚪"
                
                if cols[j].button(color, key=f"nav_{idx}"):
                    st.session_state.index = idx
                    st.session_state.last_feedback = None
                    st.rerun()

score_total = sum(1 for x in st.session_state.history if x is True)
st.write(f"**Score : {score_total} / {total_q}**")

# --- FEEDBACK ---
if st.session_state.last_feedback:
    f_type, f_msg = st.session_state.last_feedback
    if f_type == "success": st.success(f_msg)
    else: st.error(f_msg)

st.divider()

# --- QUIZ ---
if st.session_state.index < total_q:
    q = st.session_state.db[st.session_state.index]
    prompt = q["fr"] if q["dir"] == 0 else q["pt"]
    target = q["pt"] if q["dir"] == 0 else q["fr"]
    label = "Français ➔ Portugais" if q["dir"] == 0 else "Português ➔ Francês"
    
    st.write(f"Question {st.session_state.index + 1}")
    st.subheader(prompt.upper())
    st.caption(label)

    already_done = st.session_state.history[st.session_state.index] is not None

    if not already_done:
        with st.form(key='quiz_form', clear_on_submit=True):
            user_input = st.text_input("Réponse :", key="input_field")
            c1, c2 = st.columns(2)
            with c1: submit = st.form_submit_button("VALIDER")
            with c2: skip = st.form_submit_button("PASSER")

        if submit:
            dist = levenshtein(user_input, target)
            if dist <= 1:
                st.session_state.history[st.session_state.index] = True
                st.session_state.last_feedback = ("success", f"✅ Correct ! {q['fr']} = {q['pt']}")
            else:
                st.session_state.history[st.session_state.index] = False
                st.session_state.last_feedback = ("error", f"❌ Faux. La réponse était : {target}")
            st.session_state.index += 1
            st.rerun()

        if skip:
            st.session_state.history[st.session_state.index] = False
            st.session_state.last_feedback = ("error", f"Passé. La réponse était : {target}")
            st.session_state.index += 1
            st.rerun()
    else:
        # Question déjà répondue
        is_juste = st.session_state.history[st.session_state.index]
        msg = "✅ Bien joué !" if is_juste else "❌ C'était une erreur."
        st.markdown(f"### {msg}")
        st.write(f"Rappel : **{q['fr']}** = **{q['pt']}**")
        
        if st.button("Suivant ➡️"):
            st.session_state.index += 1
            st.session_state.last_feedback = None
            st.rerun()
            
    # Navigation arrière discrète
    if st.session_state.index > 0:
        if st.button("⬅️ Revenir à la question précédente"):
            st.session_state.index -= 1
            st.session_state.last_feedback = None
            st.rerun()

else:
    st.balloons()
    st.header("Fim do quiz ! 🎉")
    st.write(f"Score final : {score_total} / {total_q}")
    if st.button("Recommencer"):
        st.session_state.index = 0
        st.session_state.history = [None] * total_q
        st.rerun()

# --- SIDEBAR ---
if st.sidebar.button("🔄 Inverser tout le Quiz"):
    for item in st.session_state.db:
        item["dir"] = 1 if item["dir"] == 0 else 0
    st.session_state.index = 0
    st.session_state.history = [None] * total_q
    st.rerun()