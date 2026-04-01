import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import io

from analyseur import MOIS_FR

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


class Visualiseur:
    """
    사용법:
        vis = Visualiseur()
        buf = vis.graphique_camembert(categories)
    """

    def __init__(self):
        plt.rcParams['font.family']      = 'DejaVu Sans'
        plt.rcParams['figure.facecolor'] = '#f8f9fa'

    def _sauvegarder(self):
        """그래프를 메모리에 저장하고 반환하는 내부 함수"""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
                    bbox_inches='tight', facecolor='#f8f9fa')
        buf.seek(0)
        plt.close()
        return buf

    def graphique_camembert(self, categories, titre="Répartition des dépenses"):
        """전체 기간 파이 차트 (기존 함수 그대로 유지)"""
        labels    = list(categories.keys())
        valeurs   = [v['total'] for v in categories.values()]
        pourcents = [v['pourcentage'] for v in categories.values()]
        couleurs  = [COULEURS_CATEGORIES.get(cat, '#95a5a6') for cat in labels]

        fig, ax = plt.subplots(figsize=(9, 6))

        wedges, texts, autotexts = ax.pie(
            valeurs, labels=None, autopct='%1.1f%%',
            colors=couleurs, startangle=140,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
            pctdistance=0.82
        )
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
            autotext.set_color('white')

        legende = [
            mpatches.Patch(
                color=couleurs[i],
                label=f"{labels[i]} : {valeurs[i]:.2f}€ ({pourcents[i]}%)"
            )
            for i in range(len(labels))
        ]
        ax.legend(handles=legende, loc='center left',
                  bbox_to_anchor=(1, 0.5), fontsize=9, framealpha=0.9)
        ax.set_title(titre, fontsize=14, fontweight='bold', pad=20, color='#2c3e50')
        plt.tight_layout()
        return self._sauvegarder()

    def graphique_camembert_par_mois(self, categories_par_mois,
                                      titre="Répartition des dépenses par mois"):
        """
        ✅ 새 함수: 각 달의 파이 차트를 한 이미지에 나란히 표시

        매개변수:
            categories_par_mois = analyser_categories_par_mois() 결과
            titre               = 전체 제목

        반환값: 이미지 데이터 (BytesIO)
        """
        nb_mois = len(categories_par_mois)

        # 한 행에 최대 3개씩 배치
        nb_cols = min(3, nb_mois)
        nb_rows = math.ceil(nb_mois / nb_cols)

        fig, axes = plt.subplots(
            nb_rows, nb_cols,
            figsize=(6 * nb_cols, 6 * nb_rows)
        )

        # axes가 1개일 때도 리스트처럼 다루기 위해 변환
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

            wedges, texts, autotexts = ax.pie(
                valeurs, labels=None, autopct='%1.1f%%',
                colors=couleurs, startangle=140,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
                pctdistance=0.80
            )
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_fontweight('bold')
                autotext.set_color('white')

            # 각 파이 차트 제목 = 월 이름
            ax.set_aspect('equal')  
            ax.set_title(mois, fontsize=13, fontweight='bold', color='#2c3e50', pad=2)

            # 총 지출 금액 표시
            total = sum(valeurs)
            ax.text(0, -1.2, f"Total : {total:.2f}€",
                    ha='center', fontsize=11, color='#7f8c8d')

        # 범례는 마지막 차트 옆에 한 번만 표시
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

        # 빈 칸 숨기기 (마지막 행에 빈 subplot이 있을 때)
        for idx in range(nb_mois, nb_rows * nb_cols):
            row = idx // nb_cols
            col = idx % nb_cols
            axes[row][col].set_visible(False)

        plt.tight_layout()
        return self._sauvegarder()

    def graphique_barres_budget(self, comparaison, titre="Budget vs Dépenses réelles"):
        """예산과 실제 지출을 나란히 비교하는 막대그래프"""
        categories = list(comparaison.keys())
        budgets    = [v['budget_total']   for v in comparaison.values()]
        depenses   = [v['depense_totale'] for v in comparaison.values()]

        x = range(len(categories))

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_facecolor('#f0f0f0')

        bars1 = ax.bar([i - 0.2 for i in x], budgets,  0.35,
                       label='Budget',           color='#3498db', alpha=0.85, edgecolor='white')
        bars2 = ax.bar([i + 0.2 for i in x], depenses, 0.35,
                       label='Dépenses réelles', color='#e74c3c', alpha=0.85, edgecolor='white')

        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f'{bar.get_height():.0f}€', ha='center', va='bottom',
                    fontsize=8, color='#3498db', fontweight='bold')
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f'{bar.get_height():.0f}€', ha='center', va='bottom',
                    fontsize=8, color='#e74c3c', fontweight='bold')

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
        """카테고리별 월별 지출 추세 선 그래프"""
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.set_facecolor('#f0f0f0')

        for categorie in tendances['Catégorie'].unique():
            data_cat = tendances[tendances['Catégorie'] == categorie].copy()
            data_cat = data_cat.sort_values(['Année', 'Mois'])

            labels_x = [
                f"{MOIS_FR[row['Mois']][:3]}\n{row['Année']}"
                for _, row in data_cat.iterrows()
            ]
            x       = range(len(labels_x))
            couleur = COULEURS_CATEGORIES.get(categorie, '#95a5a6')

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
        """저축 목표 달성률 가로 막대"""
        fig, ax = plt.subplots(figsize=(8, 2))

        pourcentage = epargne['pourcentage_atteint']
        accumulated = epargne['epargne_accumulee']
        objectif    = epargne['objectif']

        ax.barh(0, objectif, height=0.5,
                color='#ecf0f1', edgecolor='#bdc3c7', linewidth=1.5)
        couleur = '#2ecc71' if pourcentage >= 100 else '#3498db'
        ax.barh(0, accumulated, height=0.5, color=couleur, alpha=0.85)

        ax.text(objectif / 2, 0, f"{pourcentage}%",
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='white' if pourcentage > 30 else '#2c3e50')
        ax.text(0,        -0.45, "0€",               ha='left',  va='top', fontsize=9, color='#7f8c8d')
        ax.text(objectif, -0.45, f"{objectif:.0f}€", ha='right', va='top', fontsize=9, color='#7f8c8d')
        ax.text(accumulated, 0.35, f"{accumulated:.0f}€ économisés",
                ha='center', va='bottom', fontsize=10,
                fontweight='bold', color='#2c3e50')

        ax.set_xlim(0, objectif * 1.05)
        ax.set_ylim(-0.6, 0.7)
        ax.axis('off')
        ax.set_title(titre, fontsize=12, fontweight='bold', color='#2c3e50', pad=15)

        plt.tight_layout()
        return self._sauvegarder()