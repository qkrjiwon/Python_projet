import pandas as pd

# Dictionnaire des catégories avec leurs mots-clés associés
# Si un mot-clé est trouvé dans le libellé d'une transaction, elle est classée dans la catégorie correspondante
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

# Liste des mots-clés permettant d'identifier un virement de salaire
SALAIRE = ['SALAIRE', 'VIREMENT SALAIRE', 'PAIE', 'TRAITEMENT']

#Classe chargée de lire et préparer les données d'un fichier CSV bancaire.
class LecteurCSV:

    # Constructeur de la classe — exécuté automatiquement à la création de l'objet.
    def __init__(self, chemin_fichier: str):
        self.chemin_fichier = chemin_fichier
        self.donnees = None

    # Détermine la catégorie d'une transaction en cherchant des mots-clés dans son libellé.
    # Retourne : Le nom de la catégorie correspondante, ou 'Autre' si aucun mot-clé ne correspond.
    def _classifier_categorie(self, libelle: str) -> str:

        libelle_upper = libelle.upper()
        for categorie, mots_cles in CATEGORIES.items():
            for mot in mots_cles:
                if mot.upper() in libelle_upper:
                    return categorie
        return 'Autre'
    
    # Vérifie si une transaction correspond à un virement de salaire.
    # Retourne : True si c'est un salaire, False sinon.
    def _est_salaire(self, libelle: str) -> bool:

        libelle_upper = libelle.upper()
        for mot in SALAIRE:
            if mot.upper() in libelle_upper:
                return True
        return False

    # Lit le fichier CSV et retourne les données sous forme de DataFrame pandas.
    # Retourne : Un DataFrame pandas, ou None en cas d'erreur.
    def lire(self):
        """
        Traitement effectué :
            - Détection de la colonne de libellé
            - Conversion de la colonne Date en format date
            - Ajout des colonnes Année et Mois
            - Conservation de toutes les transactions (dépenses et revenus)
            - Ajout d'une colonne Montant_abs (valeur absolue des dépenses)
            - Classement des dépenses par catégorie
            - Identification des virements de salaire
            
        """
        try:
            df = pd.read_csv(self.chemin_fichier, sep=';', encoding='utf-8-sig')

            # Détection du nom de la colonne contenant les libellés
            NOMS_POSSIBLES = ['Libellé', 'Libelle', 'Description',
                              'Intitulé', 'Intitule', 'Opération']
            colonne_libelle = None
            for nom in NOMS_POSSIBLES:
                if nom in df.columns:
                    colonne_libelle = nom
                    break # On s'arrête dès qu'on trouve le bon nom
            
            # Si aucune colonne de libellé n'est trouvée, on affiche les colonnes disponibles
            if colonne_libelle is None:
                print("Colonne de description introuvable.")
                print(f"Colonnes disponibles : {list(df.columns)}")
                return None

            # Conversion de la colonne Date en format date (au lieu d'une simple chaîne de caractères) pour faire des analyses temporelles (ex: dépense par mois)
            df['Date'] = pd.to_datetime(df['Date'])
            df['Année'] = df['Date'].dt.year # Extraction de l'année
            df['Mois'] = df['Date'].dt.month # Extraction du mois

            # On conserve toutes les lignes (dépenses ET revenus)
            df = df.copy()

            # Ajout d'une colonne avec le montant en valeur absolue uniquement pour les dépenses
            # Les revenus auront NaN dans cette colonne (non concernés)
            df['Montant_abs'] = df['Montant'].where(df['Montant'] < 0).abs()

            # Classification des transactions par catégorie
            # Les dépenses reçoivent une catégorie via _classifier_categorie()
            # Les revenus  reçoivent la catégorie 'Revenu'
            if 'Catégorie' not in df.columns:
                df['Catégorie'] = df.apply(
                    lambda row: self._classifier_categorie(str(row[colonne_libelle]))
                    if row['Montant'] < 0 else 'Revenu',
                    axis=1 # on applique la fonction ligne par ligne
                )

            # Ajout d'une colonne indiquant si la transaction est un salaire (True/False)
            # Ici, on ne vérifie que les revenus
            df['est_salaire'] = df.apply(
                lambda row: self._est_salaire(str(row[colonne_libelle]))
                if row['Montant'] > 0 else False,
                axis=1 
            )

            # Sauvegarde des données dans l'attribut de l'objet
            self.donnees = df

            # Affichage d'un résumé dans le terminal
            nb_depenses = len(df[df['Montant'] < 0])
            nb_revenus  = len(df[df['Montant'] > 0])
            print(f"{nb_depenses} dépenses et {nb_revenus} revenus trouvés")
            return df
        
        # Le fichier CSV n'existe pas à l'emplacement indiqué
        except FileNotFoundError:
            print(f"Fichier introuvable : {self.chemin_fichier}")
            return None
        
        # Toute autre erreur inattendue (format incorrect, colonnes manquantes, etc.)
        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
            return None