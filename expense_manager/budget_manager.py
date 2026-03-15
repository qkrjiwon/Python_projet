"""
Module de gestion du budget et de l'épargne.
Responsabilité : Comparer les dépenses réelles au budget défini,
calculer l'épargne cumulée et la progression vers l'objectif.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class BudgetManager:
    """
    Gère la logique budgétaire et d'épargne.
    
    Pourquoi séparer ce module ?
    → La logique financière est indépendante de l'affichage
    → Facilite les tests et la maintenance
    → Permet de réutiliser ces calculs dans d'autres contextes
    """

    def __init__(self):
        self.category_budgets: Dict[str, float] = {}  # Budget par catégorie
        self.savings_goal_annual: float = 0.0          # Objectif épargne annuel
        self.savings_goal_monthly: float = 0.0         # Objectif épargne mensuel
        self.total_budget_monthly: float = 0.0         # Budget total mensuel

    # ─────────────────────────────────────────────
    # CONFIGURATION DU BUDGET
    # L'utilisateur définit ses limites par catégorie
    # et son objectif d'épargne annuel
    # ─────────────────────────────────────────────
    def set_budget(self, category_budgets: Dict[str, float],
                   savings_goal_annual: float) -> None:
        """
        Configure le budget mensuel par catégorie et l'objectif d'épargne.
        
        Args:
            category_budgets    : {'Loyer': 1000, 'Shopping': 100, ...}
            savings_goal_annual : Montant à épargner sur l'année (ex: 2400)
        
        Logique :
        - Budget total mensuel = somme des budgets par catégorie
        - Objectif mensuel = objectif annuel / 12
        - Le budget total doit couvrir les dépenses ET l'épargne mensuelle
        """
        self.category_budgets = category_budgets
        self.savings_goal_annual = savings_goal_annual

        # Objectif d'épargne mensuel = objectif annuel / 12
        self.savings_goal_monthly = round(savings_goal_annual / 12, 2)
        # Budget mensuel total = somme des budgets de toutes les catégories
        self.total_budget_monthly = sum(category_budgets.values())

    # ─────────────────────────────────────────────
    # Comparaison entre le budget prévu et les dépenses réelles
    # Calcul du dépassement ou du solde restant par catégorie
    # ─────────────────────────────────────────────
    def evaluate_budget(self, actual_expenses: Dict[str, float],
                        month_label: str = None) -> pd.DataFrame:
        """
        Compare les dépenses réelles au budget et retourne le résultat

        Returns:
            DataFrame avec les colonnes :
            - catégorie, budget, réel, différence, statut, pourcentage_utilisé
        """
        results = []

        # Parcours de toutes les catégories pour lesquelles un budget est défini
        for category, budget in self.category_budgets.items():
            # Dépenses réelles (0 par défaut si aucune dépense)
            actual = actual_expenses.get(category, 0.0)

            # Différence = budget - dépenses réelles
            # Positif → dans le budget (économie réalisée)
            # Négatif → dépassement du budget
            difference = budget - actual

            # Taux d'utilisation du budget (%)
            pct_used = round((actual / budget * 100), 1) if budget > 0 else 0

            # Détermination du statut
            if difference > 0:
                statut = "✅ Sous budget"
            elif difference == 0:
                statut = "🟡 Exact"
            else:
                statut = "❌ Dépassement"

            results.append({
                'catégorie': category,
                'budget (€)': round(budget, 2),
                'réel (€)': round(actual, 2),
                'différence (€)': round(difference, 2),
                'utilisé (%)': pct_used,
                'statut': statut
            })

        return pd.DataFrame(results)

    # ─────────────────────────────────────────────
    # Calcul de l'épargne cumulée
    # Cumul des économies réalisées chaque mois
    # et suivi de la progression vers l'objectif
    # ─────────────────────────────────────────────
    def compute_savings_progress(self,
                                  monthly_totals: pd.DataFrame) -> dict:
        """
        Calcul de l'épargne cumulée mois par mois

        Args:
            monthly_totals : DataFrame avec les colonnes ['mois', 'total_mensuel']

        Returns:
            dict contenant les détails de l'épargne
        """
        savings_per_month = []

        for _, row in monthly_totals.iterrows():
            # Épargne du mois = budget total - dépenses réelles du mois
            monthly_saving = self.total_budget_monthly - row['total_mensuel']
            savings_per_month.append({
                'mois': str(row['mois']),
                'dépenses': round(row['total_mensuel'], 2),
                'épargne_mois': round(monthly_saving, 2)
            })

        savings_df = pd.DataFrame(savings_per_month)

        # Épargne cumulée mois après mois
        savings_df['épargne_cumulée'] = savings_df['épargne_mois'].cumsum().round(2)

        # Montant restant à épargner pour atteindre l'objectif
        total_saved = savings_df['épargne_cumulée'].iloc[-1]
        remaining = self.savings_goal_annual - total_saved

        return {
            'savings_df': savings_df,
            'total_saved': round(total_saved, 2),
            'remaining': round(remaining, 2),
            'goal': self.savings_goal_annual,
            'monthly_goal': self.savings_goal_monthly,
            'progress_pct': round((total_saved / self.savings_goal_annual * 100), 1)
            if self.savings_goal_annual > 0 else 0
        }
