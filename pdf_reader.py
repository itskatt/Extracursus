import io
import re

from PyPDF4 import PdfFileReader

SUBJECTS_REGEX = re.compile(r"Code (UE|Matière) .+\d :")
COMMENTS_REGEX = re.compile(r"Séance.+-")
GRADE_REGEX = re.compile(r"((\d+\.\d+) \(.+ (\d+\.\d+)\))|(Résultats non publiés)") # note (et coeff)


def remove0s(float_):
    return str(float_).rstrip("0").rstrip(".")

def extract_text(pdf):
    with io.BytesIO(pdf) as f:
        reader = PdfFileReader(f)

        # extraction et premier filtrage du texte
        text = []
        for page in range(reader.getNumPages()):
            page = reader.getPage(page).extractText().splitlines()
            page = page[1:-3]  # on enleve les trucs inutiles
            text.append("\n".join([line.strip() for line in page]))

    return "\n".join(text)

def extract_subjects(text):
    out = []
    # extraction des notes par matiere
    subjects = [m.start() for m in SUBJECTS_REGEX.finditer(text)]
    for i in range(len(subjects) - 1):
        subject = text[subjects[i]:subjects[i + 1]]
        subject = subject.splitlines()

        # 1ere ligne: nom de la matiere
        name = subject[0].split(" : ")[-1]

        # 2nde ligne: nom du prof + moeynne de la matiere
        # prof
        if "Responsable" in subject[1]:
            teacher = subject[1].split(" : ")[-1]
        else:
            teacher = "Pas de prof"
        # moyenne
        if "Moyenne" in subject[1]:
            average = remove0s(subject[1].split(" : ")[1].split(" ")[0])
        else:
            # average = "Pas de moyenne disponible sur le PDF"
            average = None

        # le reste : les notes
        # d'abbord on essaye de determiner le nombre de notes
        grades_text = subject[3:]

        # extraction des notes
        raw_grades = [GRADE_REGEX.match(line) for line in grades_text]

        # filtrage des notes
        grades = []
        for match in filter(lambda g: g is not None, raw_grades):
            if match.groups()[-1] is None: # note + coef
                grades.append((
                    float(match.group(2)), # note
                    float(match.group(3)) # coef
                ))
            else: # "Résultats non publiés"
                grades.append((match.group(),))

        # calcul de la moyenne si elle n'apparait pas sur le PDF
        if not average:
            filtered = list(filter(lambda g: len(g) > 1, grades))
            if filtered: # on calcule la moyenne uniquement si on a des notes
                average = sum((g[0] * g[1] for g in filtered)) / sum((g[1] for g in filtered))
                average = f"{remove0s(round(average, 3))} (calculée)"
            else:
                average = "Pas de moyenne disponible"

        # text des commentaires
        comments_text = "\n".join(grades_text[:-len(grades)])

        # extraction des commentaires
        comments = []
        comments_ind = [m.start() for m in COMMENTS_REGEX.finditer(comments_text)]
        comments_ind.append(len(comments_text))
        for i in range(len(comments_ind) - 1):
            comment = comments_text[comments_ind[i]:comments_ind[i + 1]]
            comments.append(comment.replace("\n", " "))

        # on enelve les 0s inutiles a la fin des notes et coefs
        grades = ((
            remove0s(pair[0]),
            remove0s(pair[1])
        )  if len(pair) == 2 else pair for pair in grades)

        # correspondance du commentaire avec la note
        grades = list(zip(comments, grades))

        out.append({
            "name": name,
            "teacher": teacher,
            "average": average,
            "grades": grades,
            "empty": "empty" if grades == [("Séance N°1 - Séance N°1", ("Résultats non publiés",))] else ""
        })

    return out

def get_grades(pdf):
    return extract_subjects(extract_text(pdf))


# For testing
if __name__ == "__main__":
    from pprint import pprint

    with open("../semestre_TBFS2t.pdf", "rb") as f:
        pdf = f.read()

    grades = get_grades(pdf)
    # grades = extract_text(pdf)
    pprint(grades)
