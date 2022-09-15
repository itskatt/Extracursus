from requests import Session


class IntraClient:
    """
    Un client pour se connecter a intracursus
    """
    def __init__(self):
        self.sess = Session()
        self.sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          "(KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        })
        self.semesters = []
        self.current_sem_exists = False

    def close(self):
        self.sess.close()

    def login(self, username, password):
        """
        Authentification sur login.unice.fr
        """
        resp = self.sess.get("https://login.unice.fr/login?service=https://ent.unice.fr/uPortal/Login")
        html_page = resp.text

        # trois valeurs importantes
        route_login = html_page.split('<form id="fm1" action="')[1].split('"')[0]
        lt = html_page.split('type="hidden" name="lt" value="')[1].split('"')[0]
        execution = html_page.split('type="hidden" name="execution" value="')[1].split('"')[0]

        payload = {
            "username": username,
            "password": password,

            "lt": lt,
            "execution": execution,
            "_eventId": "submit",
            "submit": "SE CONNECTER"
        }

        resp = self.sess.post(
            f"https://login.unice.fr{route_login}", data=payload, allow_redirects=False)

        # si on a donné des mauvais identifiants
        if "Location" not in resp.headers:
            return False

        url_location = resp.headers["Location"]
        resp = self.sess.get(url_location)

        ticket = url_location.split('ticket=')[1]
        self.sess.cookies.set("SESSID", ticket, domain="planier.unice.fr")
        return True

    def get_semesters(self):
        """
        Se connecte a intracursus et renvoie la liste des des semestres disponible
        """
        # connection a intracursus
        resp = self.sess.get(
            "https://login.unice.fr/login?service=https%3A%2F%2Fintracursus2.unice.fr%2Fic%2Fdlogin%2Fcas.php")
        html_page = resp.text

        semesters = []
        # recuperation du semestre actuel
        # il se peut qu'il n'existe pas
        try:
            semesters.append(html_page.split("<b>Relevé des notes et absences de ")[1].split()[0])
            self.current_sem_exists = True
        except IndexError:
            pass

        # recuperation des autres semestres
        try:
            raw_semesters = html_page.split(
                '<select id="idautreinscription" name="idautreinscription" size="1">')[1].split("</select>")[0].strip()
            for line in raw_semesters.splitlines():
                semesters.append(
                    line.split('value="')[1].split('"')[0]
                )
        except Exception: # on a pas pu trouver d'autres semestres
            pass

        self.semesters = semesters
        return semesters

    def get_semester_pdf(self, semester):
        # semestre actuel
        if semester == self.semesters[0] and self.current_sem_exists:
            payload = {
            "telrelevepresences": f"Télécharger le relevé des notes et absences de {semester}"
        }
        # autre semestre
        else:
            payload = {
                "idautreinscription": semester,
                "telreleveanterieur": "Télécharger le relevé du parcours sélectionné"
            }

        # téléchargement...
        resp = self.sess.post(
            "https://intracursus2.unice.fr/ic/etudiant/ic-notes-presences.php",
            data=payload
        )
        return resp.content
