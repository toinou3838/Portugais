from verbecc import Conjugator
import json
import random

pt = Conjugator(lang="pt")
fr = Conjugator(lang="fr")

verbs = {
"falar":"parler",
"comer":"manger",
"abrir":"ouvrir",
"estudar":"étudier",
"beber":"boire",
"partir":"partir",
"trabalhar":"travailler",
"vender":"vendre",
"dividir":"diviser",
"ajudar":"aider",
"correr":"courir",
"assistir":"regarder",
"comprar":"acheter",
"escrever":"écrire",
"decidir":"décider",
"lavar":"laver",
"aprender":"apprendre",
"unir":"unir",
"caminhar":"marcher",
"receber":"recevoir",
"ser":"être",
"estar":"être",
"ter":"avoir",
"ir":"aller",
"ler":"lire",
"dar":"donner",
"sair":"sortir",
"fazer":"faire",
"dizer":"dire",
"poder":"pouvoir",
"saber":"savoir",
"trazer":"apporter",
"querer":"vouloir",
"vir":"venir",
"ver":"voir"
}

persons = {
"eu":"je",
"ele":"il",
"nós":"nous",
"eles":"ils"
}

tenses = [
("indicative","present"),
("indicative","preterite"),
("indicative","imperfect"),
("indicative","future"),
("conditional","present"),
("subjunctive","present")
]

dataset = []

for v_pt, v_fr in verbs.items():

    c_pt = pt.conjugate(v_pt)
    c_fr = fr.conjugate(v_fr)

    for mood, tense in tenses:

        for p_pt, p_fr in persons.items():

            try:

                pt_form = c_pt[mood][tense][p_pt]
                fr_form = c_fr[mood][tense][p_fr]

                dataset.append({
                    "fr": f"{p_fr} {fr_form}",
                    "pt": f"{p_pt} {pt_form}",
                    "dir": random.randint(0,1)
                })

            except:
                pass

with open("verbs_dataset.json","w",encoding="utf-8") as f:
    json.dump(dataset,f,ensure_ascii=False,indent=2)

print(len(dataset),"phrases générées")