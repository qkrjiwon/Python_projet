import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import io

from analyseur import MOIS_FR

# Couleurs pour chaque catégorie (pour les graphiques)
COULEURS_CATEGORIES = {
    'Transport':          '#3498db',
    'Alimentation':       '#2ecc71',
    'Logement':           '#e74c3c',
    'Shopping':           '#f39c12',
    'Loisirs':            '#9b59b6',
    'Remboursement prêt': '#1abc9c',
    'Santé':              '#e67e22',
    'Autre':              '#95a5a6'
}

# Classe qui génère des graphiques financiers pour le rapport PDF.
class Visualiseur:
    
    def __init__(self):
        # Configuration globale du style des graphiques
        plt.rcParams['font.family']      = 'DejaVu Sans'
        plt.rcParams['figure.facecolor'] = '#f8f9fa'

    def _sauvegarder(self):
        """Sauvegarde le graphique en mémoire et le retourne."""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
                    bbox_inches='tight', facecolor='#f8f9fa')
        buf.seek(0)
        plt.close()
        return buf

    def graphique_camembert_par_mois(self, categories_par_mois,
                                      titre="Répartition des dépenses par mois"):
        """
        Affiche un camembert par mois côte à côte dans une seule image.

        Paramètres :
            categories_par_mois = résultat de analyser_categories_par_mois()
            titre = titre global

        Retourne : image (BytesIO)
        """
        nb_mois = len(categories_par_mois)

        # Disposition : maximum 3 graphiques par ligne
        nb_cols = min(3, nb_mois)
        nb_rows = math.ceil(nb_mois / nb_cols)

        # Taille des graphiques : 6x6
        fig, axes = plt.subplots(
            nb_rows, nb_cols,
            figsize=(6 * nb_cols, 6 * nb_rows)
        )

        # Conversion en liste si un seul graphique (un seul mois) pour itérer facilement
        if nb_mois == 1:
            axes = [[axes]]
        elif nb_rows == 1:
            axes = [axes]

        mois_liste = list(categories_par_mois.items())

        for idx, (mois, categories) in enumerate(mois_liste):
            row = idx // nb_cols
            col = idx % nb_cols
            ax  = axes[row][col]

            labels    = list(categories.keys())
            valeurs   = [v['total'] for v in categories.values()]
            couleurs  = [COULEURS_CATEGORIES.get(cat, '#95a5a6') for cat in labels]

            # Dessin du camembert (pie chart)
            wedges, texts, autotexts = ax.pie(
                valeurs, labels=None, autopct='%1.1f%%',
                colors=couleurs, startangle=140,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
                pctdistance=0.80
            )
            # Mise en forme du texte du pourcentage à l'intérieur des parts
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_fontweight('bold')
                autotext.set_color('white')

            # Titre de chaque camembert = nom du mois
            ax.set_aspect('equal')  
            ax.set_title(mois, fontsize=13, fontweight='bold', color='#2c3e50', pad=2)

            # Affichage du montant total dépensé sous chaque camembert
            total = sum(valeurs)
            ax.text(0, -1.2, f"Total : {total:.2f}€",
                    ha='center', fontsize=11, color='#7f8c8d')

        # Création d'une légende globale en bas de l'image
        if mois_liste:
            last_categories = mois_liste[-1][1]
            labels_leg  = list(last_categories.keys())
            couleurs_leg = [COULEURS_CATEGORIES.get(cat, '#95a5a6') for cat in labels_leg]
            legende = [
                mpatches.Patch(color=couleurs_leg[i], label=labels_leg[i])
                for i in range(len(labels_leg))
            ]
            fig.legend(handles=legende, loc='lower center',
                       ncol=len(labels_leg),
                       fontsize=11, framealpha=0.9,
                       bbox_to_anchor=(0.5, -0.08))

        # Masquer les cases vides (si la dernière ligne n'est pas complète)
        for idx in range(nb_mois, nb_rows * nb_cols):
            row = idx // nb_cols
            col = idx % nb_cols
            axes[row][col].set_visible(False)

        plt.tight_layout()
        return self._sauvegarder()

    def graphique_barres_budget(self, comparaison, titre="Budget vs Dépenses réelles"):
        """Graphique à barres comparant le budget et les dépenses réelles."""
        categories = list(comparaison.keys())
        budgets    = [v['budget_total']   for v in comparaison.values()]
        depenses   = [v['depense_totale'] for v in comparaison.values()]

        x = range(len(categories))

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_facecolor('#f0f0f0')

        # On dessine les deux barres décalées de 0.2 pour qu'elles soient côte à côte
        bars1 = ax.bar([i - 0.2 for i in x], budgets,  0.35,
                       label='Budget',           color='#3498db', alpha=0.85, edgecolor='white')
        bars2 = ax.bar([i + 0.2 for i in x], depenses, 0.35,
                       label='Dépenses réelles', color='#e74c3c', alpha=0.85, edgecolor='white')

        # Ajout des étiquettes de montant au-dessus des barres
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f'{bar.get_height():.0f}€', ha='center', va='bottom',
                    fontsize=8, color='#3498db', fontweight='bold')
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f'{bar.get_height():.0f}€', ha='center', va='bottom',
                    fontsize=8, color='#e74c3c', fontweight='bold')

        # Configuration des axes (noms des catégories, légendes)
        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, rotation=15, ha='right', fontsize=9)
        ax.set_ylabel('Montant (€)', fontsize=10)
        ax.set_title(titre, fontsize=13, fontweight='bold', color='#2c3e50')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.4, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return self._sauvegarder()

    def graphique_tendances(self, tendances, titre="Tendances des dépenses par catégorie"):
        """Graphique linéaire montrant l'évolution mensuelle par catégorie."""
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.set_facecolor('#f0f0f0')

        # Trace une courbe par catégorie
        for categorie in tendances['Catégorie'].unique():
            data_cat = tendances[tendances['Catégorie'] == categorie].copy()
            data_cat = data_cat.sort_values(['Année', 'Mois'])

            # Préparation des étiquettes de l'axe X (ex: "Jan 2024")
            labels_x = [
                f"{MOIS_FR[row['Mois']][:3]}\n{row['Année']}"
                for _, row in data_cat.iterrows()
            ]
            x       = range(len(labels_x))
            couleur = COULEURS_CATEGORIES.get(categorie, '#95a5a6')

            # Dessin de la courbe avec des petits ronds (markers) sur les points
            ax.plot(list(x), data_cat['Montant_abs'].values,
                    marker='o', label=categorie,
                    color=couleur, linewidth=2.2,
                    markersize=7, markerfacecolor='white',
                    markeredgecolor=couleur, markeredgewidth=2)

            ax.set_xticks(list(x))
            ax.set_xticklabels(labels_x, fontsize=8)

        ax.set_ylabel('Montant (€)', fontsize=10)
        ax.set_title(titre, fontsize=13, fontweight='bold', color='#2c3e50')
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
        ax.grid(True, alpha=0.35, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return self._sauvegarder()

    def graphique_epargne(self, epargne, titre="Progression de l'épargne"):
        """Barre horizontale montrant le taux de réussite de l'objectif d'épargne."""
        fig, ax = plt.subplots(figsize=(8, 2))

        pourcentage = epargne['pourcentage_atteint']
        accumulated = epargne['epargne_accumulee']
        objectif    = epargne['objectif']

        # Barre de fond (objectif)
        ax.barh(0, objectif, height=0.5,
                color='#ecf0f1', edgecolor='#bdc3c7', linewidth=1.5)
        
        # Barre de progression
        couleur = '#2ecc71' if pourcentage >= 100 else '#3498db'
        ax.barh(0, accumulated, height=0.5, color=couleur, alpha=0.85)

        # Texte au centre (pourcentage)
        ax.text(objectif / 2, 0, f"{pourcentage}%",
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='white' if pourcentage > 30 else '#2c3e50')
        
        # Étiquettes 0 et Objectif final
        ax.text(0,        -0.45, "0€",               ha='left',  va='top', fontsize=9, color='#7f8c8d')
        ax.text(objectif, -0.45, f"{objectif:.0f}€", ha='right', va='top', fontsize=9, color='#7f8c8d')
        
        # Étiquette du montant économisé actuel
        ax.text(accumulated, 0.35, f"{accumulated:.0f}€ économisés",
                ha='center', va='bottom', fontsize=10,
                fontweight='bold', color='#2c3e50')

        ax.set_xlim(0, objectif * 1.05)
        ax.set_ylim(-0.6, 0.7)
        ax.axis('off')
        ax.set_title(titre, fontsize=12, fontweight='bold', color='#2c3e50', pad=15)

        plt.tight_layout()
        return self._sauvegarder()