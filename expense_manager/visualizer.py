"""
Module de visualisation.
Responsabilité : Créer tous les graphiques de l'application.
Utilise Plotly pour des graphiques interactifs dans Streamlit.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict


# ─────────────────────────────────────────────
# Couleurs fixes par catégorie
# Permet à l'utilisateur d'identifier rapidement les catégories
# ─────────────────────────────────────────────
CATEGORY_COLORS = {
    "Loyer":          "#FF6B6B",
    "Alimentation":   "#4ECDC4",
    "Transport":      "#45B7D1",
    "Shopping":       "#96CEB4",
    "Loisirs":        "#FFEAA7",
    "Remboursement":  "#DDA0DD",
    "Santé":          "#98D8C8",
    "Abonnements":    "#F7DC6F",
    "Autre":          "#BDC3C7"
}


class Visualizer:

    # ─────────────────────────────────────────────
    # 1. Diagramme Circulaire (Pie Chart)
    # Visualisation de la répartition des dépenses par catégorie
    # ─────────────────────────────────────────────
    def plot_pie_chart(self, category_ratios: pd.DataFrame,
                       title: str = "Répartition des dépenses") -> go.Figure:
        """
        Génère un diagramme circulaire des ratios de dépenses par catégorie.

        Args:
            category_ratios : DataFrame avec ['catégorie', 'total', 'pourcentage']
        """
        colors = [
            CATEGORY_COLORS.get(cat, "#BDC3C7")
            for cat in category_ratios['catégorie']
        ]

        fig = go.Figure(data=[go.Pie(
            labels=category_ratios['catégorie'],
            values=category_ratios['total'],
            hole=0.4,           # Forme de donut pour un look plus moderne
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            textinfo='label+percent',
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Montant: %{value:.2f}€<br>"
                "Pourcentage: %{percent}<br>"
                "<extra></extra>"
            )
        )])

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            showlegend=True,
            legend=dict(orientation="v", x=1.05),
            height=450,
            margin=dict(t=60, b=20, l=20, r=20)
        )

        return fig

    # ─────────────────────────────────────────────
    # 2. Graphique Linéaire (Tendances par catégorie)
    # Affiche l'évolution mensuelle des dépenses par catégorie
    # ─────────────────────────────────────────────
    def plot_trend_lines(self, by_month_category: pd.DataFrame,
                          title: str = "Tendances des dépenses par catégorie") -> go.Figure:
        """
        Génère un graphique linéaire de l'évolution mensuelle des dépenses.

        Args:
            by_month_category : DataFrame avec ['mois', 'catégorie', 'total']
        """
        fig = go.Figure()

        categories = by_month_category['catégorie'].unique()

        for category in categories:
            cat_data = by_month_category[
                by_month_category['catégorie'] == category
            ].sort_values('mois')

            color = CATEGORY_COLORS.get(category, "#BDC3C7")

            fig.add_trace(go.Scatter(
                x=cat_data['mois'].astype(str),
                y=cat_data['total'],
                mode='lines+markers',       # Lignes + points de repère
                name=category,
                line=dict(color=color, width=2.5),
                marker=dict(
                    color=color,
                    size=8,
                    symbol='circle',
                    line=dict(color='white', width=1.5)
                ),
                hovertemplate=(
                    f"<b>{category}</b><br>"
                    "Mois: %{x}<br>"
                    "Montant: %{y:.2f}€<br>"
                    "<extra></extra>"
                )
            ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            xaxis_title="Mois",
            yaxis_title="Montant (€)",
            hovermode='x unified',
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            plot_bgcolor='rgba(240,240,240,0.3)',
            xaxis=dict(showgrid=True, gridcolor='white'),
            yaxis=dict(showgrid=True, gridcolor='white')
        )

        return fig

    # ─────────────────────────────────────────────
    # 3. Histogramme (Budget vs Réel)
    # Compare le budget prévu et les dépenses réelles côte à côte
    # ─────────────────────────────────────────────
    def plot_budget_comparison(self, budget_eval: pd.DataFrame,
                                title: str = "Budget vs Dépenses réelles") -> go.Figure:
        """
        Génère un graphique à barres comparant le budget et le réel.
        """
        fig = go.Figure()

        # Barres Budget
        fig.add_trace(go.Bar(
            name='Budget',
            x=budget_eval['catégorie'],
            y=budget_eval['budget (€)'],
            marker_color='rgba(70, 130, 180, 0.7)',
            marker_line=dict(color='rgba(70, 130, 180, 1)', width=1.5),
            hovertemplate="Budget: %{y:.2f}€<extra></extra>"
        ))

        # Barres Réel
        fig.add_trace(go.Bar(
            name='Réel',
            x=budget_eval['catégorie'],
            y=budget_eval['réel (€)'],
            marker_color=[
                'rgba(255, 99, 99, 0.8)'   # Rouge en cas de dépassement
                if row['différence (€)'] < 0
                else 'rgba(80, 200, 120, 0.8)'  # Vert en cas d'économie
                for _, row in budget_eval.iterrows()
            ],
            marker_line=dict(color='white', width=1),
            hovertemplate="Réel: %{y:.2f}€<extra></extra>"
        ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            barmode='group',
            xaxis_title="Catégorie",
            yaxis_title="Montant (€)",
            height=420,
            legend=dict(orientation="h", y=1.1),
            plot_bgcolor='rgba(240,240,240,0.3)',
            yaxis=dict(showgrid=True, gridcolor='white')
        )

        return fig

    # ─────────────────────────────────────────────
    # 4. Jauge de progression de l'épargne (Gauge Chart)
    # Visualise le taux d'atteinte de l'objectif d'épargne
    # ─────────────────────────────────────────────
    def plot_savings_gauge(self, savings_data: dict) -> go.Figure:
        """
        Génère un graphique de jauge pour l'objectif d'épargne.
        """
        pct = savings_data['progress_pct']
        total_saved = savings_data['total_saved']
        goal = savings_data['goal']

        # Changement de couleur selon le taux de réussite
        if pct >= 100:
            color = "#2ECC71"   # Vert (Objectif atteint)
        elif pct >= 60:
            color = "#F39C12"   # Orange (En cours)
        else:
            color = "#E74C3C"   # Rouge (Insuffisant)

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=total_saved,
            delta={
                'reference': goal,
                'valueformat': '.2f',
                'suffix': '€'
            },
            number={'suffix': '€', 'valueformat': '.2f'},
            title={'text': "Épargne cumulée", 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, goal], 'tickformat': '.0f'},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'steps': [
                    {'range': [0, goal * 0.5], 'color': '#FADBD8'},
                    {'range': [goal * 0.5, goal * 0.8], 'color': '#FDEBD0'},
                    {'range': [goal * 0.8, goal], 'color': '#D5F5E3'}
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': goal
                }
            }
        ))

        fig.update_layout(height=300, margin=dict(t=40, b=20, l=30, r=30))
        return fig

    # ─────────────────────────────────────────────
    # 5. Graphique d'aire cumulée (Évolution de l'épargne)
    # Visualisation de la croissance de l'épargne mois par mois
    # ─────────────────────────────────────────────
    def plot_cumulative_savings(self, savings_df: pd.DataFrame) -> go.Figure:

        """
        Génère un graphique d'aire montrant l'évolution cumulée de l'épargne.
        """
        fig = go.Figure()

        # Zone d'épargne cumulée
        fig.add_trace(go.Scatter(
            x=savings_df['mois'],
            y=savings_df['épargne_cumulée'],
            mode='lines+markers',
            name='Épargne cumulée',
            fill='tozeroy',
            line=dict(color='#2ECC71', width=2.5),
            marker=dict(size=8, color='#2ECC71'),
            hovertemplate="Mois: %{x}<br>Épargne cumulée: %{y:.2f}€<extra></extra>"
        ))

        # Barres d'épargne mensuelle
        fig.add_trace(go.Bar(
            x=savings_df['mois'],
            y=savings_df['épargne_mois'],
            name='Épargne du mois',
            marker_color=[
                'rgba(46, 204, 113, 0.6)' if v >= 0
                else 'rgba(231, 76, 60, 0.6)'
                for v in savings_df['épargne_mois']
            ],
            hovertemplate="Mois: %{x}<br>Épargne: %{y:.2f}€<extra></extra>"
        ))

        fig.update_layout(
            title=dict(text="Évolution de l'épargne", font=dict(size=18)),
            xaxis_title="Mois",
            yaxis_title="Montant (€)",
            height=400,
            barmode='overlay',
            legend=dict(orientation="h", y=1.1),
            plot_bgcolor='rgba(240,240,240,0.3)',
            yaxis=dict(showgrid=True, gridcolor='white')
        )

        return fig
