import pandas as pd

CATEGORIES = {
    'Transport': ['NAVIGO', 'BUS', 'METRO', 'TAXI', 'UBER', 'TGV', 'EUROSTAR'],
    'Alimentation': ['CARREFOUR', 'MONOPRIX', 'LIDL', 'FRANPRIX', 'PICARD',
                     'RESTAURANT', 'MCDO', 'STARBUCKS', 'BOULANGERIE', 'SUPERMARCHE'],
    'Logement': ['LOYER', 'CHARGES', 'EDF', 'ELECTRICITE', 'EAU',
                 'INTERNET', 'BOUYGUES', 'ORANGE', 'FREE', 'SFR'],
    'Shopping': ['AMAZON', 'FNAC', 'ZARA', 'H&M', 'IKEA', 'PRIMARK', 'SHEIN', 'SEPHORA'],
    'Loisirs': ['NETFLIX', 'SPOTIFY', 'DEEZER', 'CINEMA', 'UGC',
                'GAUMONT', 'THEATRE', 'MUSEE', 'BOWLING', 'SPORT',
                'SALLE DE SPORT', 'STEAM', 'PLAYSTATION', 'APPLE'],
    'Remboursement prêt': ['REMBOURSEMENT', 'PRET', 'CREDIT', 'EMPRUNT'],
    'Santé': ['PHARMACIE', 'MEDECIN', 'DOCTEUR', 'HOPITAL', 'DENTISTE', 'MUTUELLE'],
}

# 월급으로 인식할 키워드
SALAIRE = ['SALAIRE', 'VIREMENT SALAIRE', 'PAIE', 'TRAITEMENT']


class LecteurCSV:
    """
    사용법:
        lecteur = LecteurCSV("mon_fichier.csv")
        donnees = lecteur.lire()
    """

    def __init__(self, chemin_fichier: str):
        self.chemin_fichier = chemin_fichier
        self.donnees = None

    def _classifier_categorie(self, libelle: str) -> str:
        """
        거래 설명을 보고 카테고리를 자동으로 정해주는 함수.
        아무 키워드도 안 맞으면 'Autre' 반환.
        """
        libelle_upper = libelle.upper()
        for categorie, mots_cles in CATEGORIES.items():
            for mot in mots_cles:
                if mot.upper() in libelle_upper:
                    return categorie
        return 'Autre'

    def _est_salaire(self, libelle: str) -> bool:
        """
        거래 설명을 보고 월급인지 판단하는 함수.
        True = 월급, False = 아님
        """
        libelle_upper = libelle.upper()
        for mot in SALAIRE:
            if mot.upper() in libelle_upper:
                return True
        return False

    def lire(self):
        """
        CSV 파일을 읽어서 데이터를 반환하는 함수.
        - 지출(마이너스): Catégorie 자동 분류
        - 수입(양수):     월급 여부 표시
        반환값: pandas DataFrame
        """
        try:
            df = pd.read_csv(self.chemin_fichier, sep=';', encoding='utf-8-sig')

            # 거래 설명 열 이름 자동 탐지
            NOMS_POSSIBLES = ['Libellé', 'Libelle', 'Description',
                              'Intitulé', 'Intitule', 'Opération', 'Operation',
                              'Motif', 'Détail', 'Detail']
            colonne_libelle = None
            for nom in NOMS_POSSIBLES:
                if nom in df.columns:
                    colonne_libelle = nom
                    break

            if colonne_libelle is None:
                print("Colonne de description introuvable.")
                print(f"Colonnes disponibles : {list(df.columns)}")
                return None

            # 날짜 변환 및 년도/월 열 추가
            df['Date'] = pd.to_datetime(df['Date'])
            df['Année'] = df['Date'].dt.year
            df['Mois'] = df['Date'].dt.month

            # ✅ 전체 데이터 보존 (지출 + 수입 모두)
            df = df.copy()

            # 지출용 양수 금액 열 추가 (수입은 NaN)
            df['Montant_abs'] = df['Montant'].where(df['Montant'] < 0).abs()

            # 카테고리 분류 (지출만)
            if 'Catégorie' not in df.columns:
                df['Catégorie'] = df.apply(
                    lambda row: self._classifier_categorie(str(row[colonne_libelle]))
                    if row['Montant'] < 0 else 'Revenu',
                    axis=1
                )

            # ✅ 월급 여부 열 추가
            df['est_salaire'] = df.apply(
                lambda row: self._est_salaire(str(row[colonne_libelle]))
                if row['Montant'] > 0 else False,
                axis=1
            )

            self.donnees = df
            nb_depenses = len(df[df['Montant'] < 0])
            nb_revenus  = len(df[df['Montant'] > 0])
            print(f"{nb_depenses} dépenses et {nb_revenus} revenus trouvés")
            return df

        except FileNotFoundError:
            print(f"Fichier introuvable : {self.chemin_fichier}")
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
            return None