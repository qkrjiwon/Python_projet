"""
Module de traitement des données bancaires importées.
Responsabilité : Lire, nettoyer et catégoriser les transactions.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re


# ─────────────────────────────────────────────
# Dictionnaire de mots-clés pour la catégorisation automatique
# Chaque catégorie contient des mots-clés typiques trouvés
# dans les libellés de relevés bancaires français
# ─────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Loyer": [
        "loyer", "rent", "bail", "propriétaire", "agence immobilière",
        "charges locatives", "syndic"
    ],
    "Alimentation": [
        "carrefour", "leclerc", "lidl", "aldi", "monoprix", "intermarché",
        "casino", "franprix", "picard", "boulangerie", "supermarché",
        "épicerie", "marché", "bio c bon", "naturalia"
    ],
    "Transport": [
        "sncf", "ratp", "navigo", "uber", "blablacar", "total", "bp",
        "shell", "esso", "station service", "parking", "péage",
        "autoroute", "taxi", "vélib", "trottinette"
    ],
    "Shopping": [
        "amazon", "zara", "h&m", "fnac", "darty", "ikea", "decathlon",
        "asos", "zalando", "cdiscount", "la redoute", "bershka",
        "primark", "uniqlo", "sephora", "marionnaud"
    ],
    "Loisirs": [
        "netflix", "spotify", "disney", "canal+", "cinema", "théâtre",
        "musée", "concert", "restaurant", "bar", "café", "mcdo",
        "mcdonald", "burger king", "kfc", "sushi", "pizzeria",
        "playstation", "steam", "jeux"
    ],
    "Remboursement": [
        "crédit", "prêt", "emprunt", "mensualité", "remboursement",
        "banque", "cetelem", "sofinco", "cofidis", "credit agricole loan",
        "intérêts", "capital"
    ],
    "Santé": [
        "pharmacie", "médecin", "docteur", "clinique", "hôpital",
        "dentiste", "opticien", "mutuelle", "assurance santé"
    ],
    "Abonnements": [
        "sfr", "orange", "bouygues", "free", "numéricable",
        "assurance", "edf", "engie", "eau", "internet"
    ],
}


class DataProcessor:
    """
    Classe principale pour le traitement des données bancaires.
    
    """

    def __init__(self):
        self.raw_data = None        # Données brutes importées
        self.clean_data = None      # Données nettoyées
        self.monthly_data = {}      # Données groupées par mois

    # ─────────────────────────────────────────────
    # LECTURE DU FICHIER
    # Supporte CSV et Excel car ce sont les formats
    # les plus courants pour les exports bancaires
    # ─────────────────────────────────────────────
    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        Charge un relevé bancaire depuis un fichier CSV ou Excel.
        
        Args:
            file_path: Chemin vers le fichier ou objet fichier (Streamlit)
        
        Returns:
            DataFrame pandas avec les données brutes
        """
        try:
            # Détection automatique du format
            if hasattr(file_path, 'name'):
                # Cas Streamlit : objet fichier uploadé
                file_name = file_path.name
            else:
                file_name = str(file_path)

            if file_name.endswith('.csv'):
                # Essai avec différents séparateurs courants en France
                # Le point-virgule est standard dans les exports bancaires français
                for sep in [';', ',', '\t']:
                    try:
                        df = pd.read_csv(
                            file_path,
                            sep=sep,
                            encoding='utf-8',
                            decimal=',',    # Format français : 1.234,56
                            thousands='.'
                        )
                        if len(df.columns) > 1:
                            break
                    except Exception:
                        continue

            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Format non supporté : {file_name}")

            self.raw_data = df
            return df

        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement : {str(e)}")

    # ─────────────────────────────────────────────
    # NORMALISATION DES COLONNES
    # Les banques n'utilisent pas les mêmes noms de colonnes
    # Cette fonction tente de les mapper vers un format standard
    # ─────────────────────────────────────────────
    def normalize_columns(self, df: pd.DataFrame,
                           date_col: str,
                           amount_col: str,
                           label_col: str,
                           type_col: str = None) -> pd.DataFrame:
        """
        Renomme et normalise les colonnes vers un format standard.
        
        Format standard attendu :
        - 'date'    : Date de la transaction
        - 'montant' : Montant (négatif = dépense, positif = crédit)
        - 'libellé' : Description de la transaction
        - 'type'    : Débit/Crédit (optionnel)
        """
        column_mapping = {
            date_col: 'date',
            amount_col: 'montant',
            label_col: 'libellé'
        }
        if type_col:
            column_mapping[type_col] = 'type'

        df = df.rename(columns=column_mapping)

        # Conversion de la date en datetime
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

        # Nettoyage du montant : suppression des espaces, conversion
        if df['montant'].dtype == object:
            df['montant'] = (
                df['montant']
                .astype(str)
                .str.replace(' ', '')
                .str.replace(',', '.')
                .str.replace('€', '')
                .astype(float)
            )

        # Suppression des lignes sans date ou montant valide
        df = df.dropna(subset=['date', 'montant'])

        # Ajout de colonnes temporelles utiles pour les analyses
        df['mois'] = df['date'].dt.to_period('M')          # Ex: 2024-01
        df['mois_label'] = df['date'].dt.strftime('%B %Y') # Ex: Janvier 2024
        df['année'] = df['date'].dt.year
        df['mois_num'] = df['date'].dt.month

        self.clean_data = df
        return df

    # ─────────────────────────────────────────────
    # CATÉGORISATION AUTOMATIQUE
    # Utilise les mots-clés pour assigner une catégorie
    # à chaque transaction selon son libellé
    # ─────────────────────────────────────────────
    def categorize_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigne automatiquement une catégorie à chaque transaction.
        
        Logique :
        1. Convertir le libellé en minuscules
        2. Chercher les mots-clés de chaque catégorie
        3. Si aucun mot-clé trouvé → "Autre"
        """
        def find_category(label: str) -> str:
            if pd.isna(label):
                return "Autre"
            
            label_lower = str(label).lower()
            
            for category, keywords in CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in label_lower:
                        return category
            
            return "Autre"

        df['catégorie'] = df['libellé'].apply(find_category)

        # Séparation dépenses / revenus
        # Les dépenses sont des montants négatifs dans la plupart des relevés
        df['est_dépense'] = df['montant'] < 0
        df['montant_abs'] = df['montant'].abs()  # Valeur absolue pour les calculs

        self.clean_data = df
        return df

    # ─────────────────────────────────────────────
    # CALCULS MENSUELS
    # Agrégation des données par mois et par catégorie
    # ─────────────────────────────────────────────
    def compute_monthly_stats(self, df: pd.DataFrame) -> dict:
        """
        Calcule les statistiques mensuelles par catégorie.
        
        Returns:
            dict avec :
            - 'by_month_category' : dépenses par mois et catégorie
            - 'monthly_totals'    : total des dépenses par mois
            - 'category_averages' : moyenne mensuelle par catégorie
        """
        # Filtrer uniquement les dépenses
        expenses = df[df['est_dépense']].copy()

        # Groupement par mois et catégorie
        by_month_cat = (
            expenses
            .groupby(['mois', 'catégorie'])['montant_abs']
            .sum()
            .reset_index()
            .rename(columns={'montant_abs': 'total'})
        )

        # Total mensuel toutes catégories confondues
        monthly_totals = (
            expenses
            .groupby('mois')['montant_abs']
            .sum()
            .reset_index()
            .rename(columns={'montant_abs': 'total_mensuel'})
        )

        # Moyenne mensuelle par catégorie (sur tous les mois disponibles)
        nb_months = expenses['mois'].nunique()
        category_totals = expenses.groupby('catégorie')['montant_abs'].sum()
        category_averages = (category_totals / nb_months).round(2)

        # Moyenne générale mensuelle
        avg_monthly = monthly_totals['total_mensuel'].mean().round(2)

        self.monthly_data = {
            'by_month_category': by_month_cat,
            'monthly_totals': monthly_totals,
            'category_averages': category_averages,
            'avg_monthly_total': avg_monthly,
            'nb_months': nb_months
        }

        return self.monthly_data

    # ─────────────────────────────────────────────
    # CALCUL DES RATIOS FINANCIERS
    # Pourcentage de chaque catégorie sur le total
    # ─────────────────────────────────────────────
    def compute_category_ratios(self, df: pd.DataFrame,
                                 selected_month: str = None) -> pd.DataFrame:
        """
        Calcule le ratio (%) de chaque catégorie sur le total des dépenses.
        
        Args:
            selected_month : Si spécifié, calcule pour ce mois uniquement
                             Sinon, calcule sur toutes les données
        
        Returns:
            DataFrame avec colonnes : catégorie, total, pourcentage
        """
        expenses = df[df['est_dépense']].copy()

        if selected_month:
            expenses = expenses[expenses['mois_label'] == selected_month]

        category_totals = (
            expenses
            .groupby('catégorie')['montant_abs']
            .sum()
            .reset_index()
            .rename(columns={'montant_abs': 'total'})
        )

        total_all = category_totals['total'].sum()

        # Calcul du pourcentage avec arrondi à 2 décimales
        category_totals['pourcentage'] = (
            (category_totals['total'] / total_all * 100)
            .round(2)
        )

        # Tri décroissant pour une meilleure lisibilité
        category_totals = category_totals.sort_values('total', ascending=False)

        return category_totals
