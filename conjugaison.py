from verbecc import CompleteConjugator, LangCodeISO639_1
import json
import random

pt = CompleteConjugator(LangCodeISO639_1.pt)
fr = CompleteConjugator(LangCodeISO639_1.fr)

verbs = {
    "falar": "parler",
    "comer": "manger",
    "abrir": "ouvrir",
    "estudar": "étudier",
    "beber": "boire",
    "partir": "partir",
    "trabalhar": "travailler",
    "vender": "vendre",
    "dividir": "diviser",
    "ajudar": "aider",
    "correr": "courir",
    "assistir": "regarder",
    "comprar": "acheter",
    "escrever": "écrire",
    "decidir": "décider",
    "lavar": "laver",
    "aprender": "apprendre",
    "unir": "unir",
    "caminhar": "marcher",
    "receber": "recevoir",
    "ser": "être",
    "estar": "être",
    "ter": "avoir",
    "ir": "aller",
    "ler": "lire",
    "dar": "donner",
    "sair": "sortir",
    "fazer": "faire",
    "dizer": "dire",
    "poder": "pouvoir",
    "saber": "savoir",
    "trazer": "apporter",
    "querer": "vouloir",
    "vir": "venir",
    "ver": "voir",
}

persons = [
    ("eu", "je"),
    ("ele", "il"),
    ("nós", "nous"),
    ("eles", "ils"),
]

tenses = [
    ("indicativo", "presente", "indicatif", "présent"),
    ("indicativo", "pretérito-perfeito", "indicatif", "passé-composé"),
    ("indicativo", "futuro-do-presente", "indicatif", "futur-simple"),
    ("condicional", "futuro-do-pretérito", "conditionnel", "présent"),
    ("indicativo", "pretérito-imperfeito", "indicatif", "imparfait"),
    ("subjuntivo", "presente", "subjonctif", "présent"),
]


def raw_value(value):
    return getattr(value, "value", value)


def get_form(forms, pronoun):
    for item in forms:
        item_pronoun = raw_value(item.get("pr"))
        if item_pronoun != pronoun:
            continue
        conjugations = item.get("c", [])
        if conjugations:
            return conjugations[0]
    raise KeyError(f"Pronoun not found: {pronoun}")


dataset = []

for v_pt, v_fr in verbs.items():
    pt_data = pt.conjugate(v_pt, conjugate_pronouns=True).get_data()["moods"]
    fr_data = fr.conjugate(v_fr, conjugate_pronouns=True).get_data()["moods"]

    for mood_pt, tense_pt, mood_fr, tense_fr in tenses:
        pt_forms = pt_data[mood_pt][tense_pt]
        fr_forms = fr_data[mood_fr][tense_fr]

        for pronoun_pt, pronoun_fr in persons:
            dataset.append(
                {
                    "fr": get_form(fr_forms, pronoun_fr),
                    "pt": get_form(pt_forms, pronoun_pt),
                    "dir": random.randint(0, 1),
                }
            )

with open("verbs_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(len(dataset), "phrases générées")
