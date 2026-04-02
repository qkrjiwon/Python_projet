# --- DICTIONNAIRE DE TRADUCTION DES MOIS ---
# On l'utilise pour transformer le chiffre du mois (1, 2...) en texte ("Janvier"...)
MOIS_FR = {
    1: 'Janvier', 2: 'Février',  3: 'Mars',     4: 'Avril',
    5: 'Mai',     6: 'Juin',     7: 'Juillet',   8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

# Classe pour analyser les données de dépenses.
class AnalyseurDepenses:

    def __init__(self, donnees):
        # On garde uniquement les lignes avec un montant négatif (= dépenses)
        self.depenses = donnees[donnees['Montant'] < 0].copy()
        # On garde uniquement les lignes avec un montant positif (= revenus)
        self.revenus  = donnees[donnees['Montant'] > 0].copy()

    # Calcul le total et le pourcentage des dépenses par catégorie (Total sur toute la période)
    # Retourne : {'Transport': {'total': 250.0, 'pourcentage': 15.5}, ...}

    def analyser_categories(self):

        # Regroupe toutes les dépenses par catégorie et additionne les montants
        par_categorie  = self.depenses.groupby('Catégorie')['Montant_abs'].sum()
        total_depenses = par_categorie.sum()

        resultats = {}
        # On boucle sur chaque catégorie pour calculer son poids (pourcentage)
        for categorie, montant in par_categorie.items():
            resultats[categorie] = {
                'total': round(montant, 2),
                'pourcentage': round((montant / total_depenses) * 100, 1)
            }
        return resultats
    
    # Calcule les proportions des catégories pour chaque mois.
    # Utile pour générer des graphiques camembert mensuels.
    # Retourne : {'Janvier 2024': {'Transport': {'total': 131, 'pourcentage': 9.6}, ...},...}
    def analyser_categories_par_mois(self):

        resultats_par_mois = {}

        # Regroupe par année et mois pour traiter chaque mois séparément
        for (annee, mois), groupe in self.depenses.groupby(['Année', 'Mois']):
            cle = f"{MOIS_FR[mois]} {annee}"

            # Dans ce mois précis, on calcule le total par catégorie
            par_categorie = groupe.groupby('Catégorie')['Montant_abs'].sum()
            total_du_mois = par_categorie.sum()

            resultats_par_mois[cle] = {}
            for categorie, montant in par_categorie.items():
                resultats_par_mois[cle][categorie] = {
                    'total': round(montant, 2),
                    'pourcentage': round((montant / total_du_mois) * 100, 1)
                }

        return resultats_par_mois
    
    # Calcule le total mensuel, la moyenne globale et le solde si un salaire est présent.
    def calculer_moyenne_mensuelle(self):
        """
        Retourne : {
            'moyenne': 1250.50,
            'a_un_salaire': True,
            'par_mois': {
                'Janvier 2024': {
                    'depenses': 1100.0,
                    'salaire':  2500.0,   # None si pas de salaire
                    'solde':    1400.0    # Salaire - Dépenses, None si pas de salaire
                }, ...
            }
        }
        """
        # Calcule le total des dépenses pour chaque mois
        par_mois_depenses = self.depenses.groupby(['Année', 'Mois'])['Montant_abs'].sum()

        # Vérification de la présence d'un salaire
        a_un_salaire = self.revenus['est_salaire'].any() if 'est_salaire' in self.revenus.columns else False

        if a_un_salaire:
            salaires = self.revenus[self.revenus['est_salaire']]
            par_mois_salaires = salaires.groupby(['Année', 'Mois'])['Montant'].sum()

        mois_dict = {}
        # On parcourt chaque mois pour construire le bilan (Dépenses vs Salaire)
        for (annee, mois), depense in par_mois_depenses.items():
            cle = f"{MOIS_FR[mois]} {annee}"

            salaire = None
            solde   = None
            if a_un_salaire:
                salaire = par_mois_salaires.get((annee, mois), None)
                if salaire is not None:
                    salaire = round(float(salaire), 2)
                    solde   = round(salaire - depense, 2) # Le solde = l'argent qui reste

            mois_dict[cle] = {
                'depenses': round(depense, 2),
                'salaire':  salaire,
                'solde':    solde
            }

        moyenne = round(par_mois_depenses.mean(), 2)
        return {
            'moyenne':      moyenne,
            'par_mois':     mois_dict,
            'a_un_salaire': a_un_salaire
        }
    
    # Compare les dépenses réelles avec le budget défini.
    # Retourne : (dictionnaire de résultats, nombre total_economise)

    def comparer_budget(self, budgets):

        par_categorie = self.depenses.groupby('Catégorie')['Montant_abs'].sum()

        # Compte le nombre de mois distincts dans les données
        nb_mois = self.depenses.groupby(['Année', 'Mois']).ngroups

        resultats      = {}
        total_economise = 0

        for categorie, budget_mensuel in budgets.items():
            depense_totale = par_categorie.get(categorie, 0)

            # Budget total = budget mensuel × nombre de mois
            budget_total = budget_mensuel * nb_mois

            # Écart positif = on a dépensé moins que prévu = économie
            # Écart négatif = on a dépensé plus que prévu = dépassement
            ecart = budget_total - depense_totale
            if ecart >= 0:
                statut = 'économie'
                total_economise += ecart
            else:
                statut = 'dépassement'

            resultats[categorie] = {
                'budget_mensuel': budget_mensuel,
                'budget_total':   round(budget_total, 2),
                'depense_totale': round(depense_totale, 2),
                'ecart':          round(abs(ecart), 2),
                'statut':         statut,
                'nb_mois':        nb_mois
            }

        return resultats, round(total_economise, 2)
    
    # Calcul du montant total épargné et du taux d'atteinte de l'objectif
    def calculer_epargne(self, budgets, objectif_epargne):

        # On récupère le montant total économisé grâce à la fonction précédente
        _, total_economise = self.comparer_budget(budgets)

        # Calcul du reste à épargner
        restant = max(0, objectif_epargne - total_economise)

        # On plafonne à 100% même si on a dépassé l'objectif
        pourcentage_atteint = min(100, round((total_economise / objectif_epargne) * 100, 1))

        return {
            'epargne_accumulee':   total_economise,
            'objectif':            objectif_epargne,
            'restant':             restant,
            'pourcentage_atteint': pourcentage_atteint
        }
    
    # Retourne les données de tendances de dépenses par catégorie et par mois.
    # Retourne : DataFrame (Catégorie, Année, Mois, Montant_abs)
    def analyser_tendances(self):

        # Transformation du résultat en un tableau simple
        tendances = self.depenses.groupby(
            ['Catégorie', 'Année', 'Mois']
        )['Montant_abs'].sum().reset_index()

        return tendances