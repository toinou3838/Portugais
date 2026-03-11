import sys
import unicodedata
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# --- BASE DE DONNÉES DES 100 QUESTIONS ---
db = [
    {"fr": "prendre un taxi", "pt": "pegar um táxi", "dir": 0},
    {"fr": "tout va bien", "pt": "tudo bem", "dir": 1},
    {"fr": "tout le livre", "pt": "todo o livre", "dir": 0},
    {"fr": "est-ce possible de ... ?", "pt": "dá para ... ?", "dir": 1},
    {"fr": "un coup de main", "pt": "dar uma mão", "dir": 0},
    {"fr": "faire une cagnotte", "pt": "fazer vaquinha", "dir": 1},
    {"fr": "au cas où", "pt": "caso", "dir": 0},
    {"fr": "prendre soin de", "pt": "zelar", "dir": 1},
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
    {"fr": "immeuble / bâtiment", "pt": "prédio", "dir": 1},
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
    {"fr": "fauché / dur", "pt": "duro", "dir": 1},
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

def normalize(text):
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace(" ", "").replace("...", "")
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

class PortugueseQuiz(QWidget):
    def __init__(self):
        super().__init__()
        self.index = 0
        self.score = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Quiz de Português")
        self.setFixedSize(600, 450)
        
        # Style sobre : Ardoise, Gris fer et Bleu sourd
        self.setStyleSheet("""
            QWidget { 
                background-color: #2b2b2b; 
                color: #dcdcdc; 
                font-family: 'Segoe UI', sans-serif; 
            }
            QLabel#info { 
                color: #888888; 
                font-size: 13px; 
            }
            QLabel#question { 
                font-size: 26px; 
                font-weight: 500; 
                color: #ffffff; 
                padding: 10px;
            }
            QLabel#sub { 
                font-size: 14px; 
                color: #4a90e2; 
                font-style: italic;
            }
            QLineEdit { 
                background-color: #3c3f41; 
                border: 1px solid #555555; 
                border-radius: 4px;
                padding: 12px; 
                font-size: 20px; 
                color: #ffffff;
                min-height: 45px; /* Correction de la taille du champ */
            }
            QLineEdit:focus { 
                border: 1px solid #4a90e2; 
            }
            QPushButton#validate { 
                background-color: #4a90e2; 
                color: white; 
                border: none;
                border-radius: 4px;
                padding: 12px; 
                font-size: 16px; 
                font-weight: bold;
            }
            QPushButton#validate:hover { 
                background-color: #357abd; 
            }
            QPushButton#skip { 
                background-color: transparent; 
                color: #777777; 
                border: 1px solid #555555;
                border-radius: 4px; 
                padding: 8px; 
                font-size: 13px;
            }
            QPushButton#skip:hover { 
                color: #bbbbbb; 
                border-color: #888888; 
            }
            QLabel#feedback { 
                font-size: 16px; 
                margin-top: 10px; 
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(15)

        self.lbl_info = QLabel("Question 1 / 100")
        self.lbl_info.setObjectName("info")
        self.lbl_info.setAlignment(Qt.AlignCenter)

        self.lbl_question = QLabel("")
        self.lbl_question.setObjectName("question")
        self.lbl_question.setAlignment(Qt.AlignCenter)
        self.lbl_question.setWordWrap(True)

        self.lbl_sub = QLabel("")
        self.lbl_sub.setObjectName("sub")
        self.lbl_sub.setAlignment(Qt.AlignCenter)

        self.input_ans = QLineEdit()
        self.input_ans.setPlaceholderText("Écrivez ici...")
        self.input_ans.returnPressed.connect(self.check_answer)

        self.btn_validate = QPushButton("VALIDER")
        self.btn_validate.setObjectName("validate")
        self.btn_validate.clicked.connect(self.check_answer)

        self.btn_skip = QPushButton("PASSER")
        self.btn_skip.setObjectName("skip")
        self.btn_skip.clicked.connect(self.skip_question)

        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setObjectName("feedback")
        self.lbl_feedback.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.lbl_info)
        layout.addWidget(self.lbl_question)
        layout.addWidget(self.lbl_sub)
        layout.addWidget(self.input_ans)
        layout.addWidget(self.btn_validate)
        layout.addWidget(self.btn_skip)
        layout.addWidget(self.lbl_feedback)
        layout.addStretch()

        self.setLayout(layout)
        self.load_question()

    def load_question(self):
        if self.index < len(db):
            q = db[self.index]
            text = q["fr"] if q["dir"] == 0 else q["pt"]
            lang = "Français ➔ Portugais" if q["dir"] == 0 else "Português ➔ Francês"
            self.lbl_question.setText(text.upper())
            self.lbl_sub.setText(lang)
            self.lbl_info.setText(f"QUESTION {self.index + 1} / {len(db)}")
            self.input_ans.clear()
            self.input_ans.setFocus()
        else:
            QMessageBox.information(self, "Fim!", f"Quiz terminé !\nScore final : {self.score}/{len(db)}")
            self.close()

    def check_answer(self):
        user_val = self.input_ans.text().strip()
        if not user_val: return

        q = db[self.index]
        target = q["pt"] if q["dir"] == 0 else q["fr"]

        dist = levenshtein(user_val, target)

        if dist <= 1:
            self.score += 1
            self.lbl_feedback.setText(f"✅ Correct ! ({target})")
            self.lbl_feedback.setStyleSheet("color: #27ae60;") # Vert sobre
            self.index += 1
            self.load_question()
        else:
            self.lbl_feedback.setText(f"❌ Erreur. La réponse était : {target}")
            self.lbl_feedback.setStyleSheet("color: #e74c3c;") # Rouge sobre
            self.input_ans.clear()

    def skip_question(self):
        q = db[self.index]
        target = q["pt"] if q["dir"] == 0 else q["fr"]
        self.lbl_feedback.setText(f"Passé. La réponse était : {target}")
        self.lbl_feedback.setStyleSheet("color: #f39c12;") # Orange sobre
        self.index += 1
        self.load_question()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PortugueseQuiz()
    window.show()
    sys.exit(app.exec())