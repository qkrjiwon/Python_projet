# =============================================================
# main.py
# 역할: 프로그램 시작점 — 모든 클래스를 import해서 순서대로 실행
#
# 실행 방법 (VS Code 터미널에서):
#   python main.py
# =============================================================

# ↓ 같은 폴더의 파일들에서 클래스 가져오기
from lecteur_csv   import LecteurCSV          # lecteur_csv.py
from analyseur      import AnalyseurDepenses   # analyseur.py
from visualiseur    import Visualiseur         # visualiseur.py
from generateur_pdf import GenerateurPDF       # generateur_pdf.py


# =============================================================
# ⚙️ 설정 — 여기만 수정하면 됩니다!
# =============================================================

CHEMIN_CSV = "transactions.csv"
 
MES_BUDGETS = {
    'Transport':          150,
    'Alimentation':       250,
    'Logement':           750,
    'Shopping':            80,
    'Loisirs':             60,
    'Remboursement prêt': 200,
}
 
OBJECTIF_EPARGNE = 1500.0
CHEMIN_PDF       = "rapport_budget.pdf"
  
# =============================================================
if __name__ == "__main__":
 
    print("=" * 55)
    print("   GESTION BUDGET PERSONNEL - 가계부 프로그램")
    print("=" * 55)
 
    # 1단계: CSV 읽기
    print("\n Lecture du fichier CSV...")
    lecteur = LecteurCSV(CHEMIN_CSV)
    donnees = lecteur.lire()
 
    if donnees is None:
        print("Impossible de lire le fichier. Programme arrêté.")
        exit()
 
    # 2단계: 분석
    print("\n Analyse des données...")
    analyseur = AnalyseurDepenses(donnees)
 
    categories              = analyseur.analyser_categories()
    categories_par_mois     = analyseur.analyser_categories_par_mois()  
    moyenne                 = analyseur.calculer_moyenne_mensuelle()
    comparaison, economise  = analyseur.comparer_budget(MES_BUDGETS)
    epargne                 = analyseur.calculer_epargne(MES_BUDGETS, OBJECTIF_EPARGNE)
    tendances               = analyseur.analyser_tendances()
 
    # 3단계: 터미널 출력
    print("\n --- RÉSULTATS ---")
    print(f"  Dépense mensuelle moyenne : {moyenne['moyenne']:.2f}€")
    print(f"  Épargne accumulée : {epargne['epargne_accumulee']:.2f}€ / {OBJECTIF_EPARGNE:.0f}€")
 
    print("\n  Détail par catégorie :")
    for cat, vals in categories.items():
        print(f"    - {cat}: {vals['total']:.2f}€ ({vals['pourcentage']}%)")
 
    print("\n  Respect du budget :")
    for cat, vals in comparaison.items():
        if vals['statut'] == 'économie':
            print(f"    OK  {cat}: économie de {vals['ecart']:.2f}€")
        else:
            print(f"    !!  {cat}: dépassement de {vals['ecart']:.2f}€")
 
    # 월급/잔액 출력 (있을 때만)
    if moyenne.get('a_un_salaire'):
        print("\n  Salaire et solde mensuel :")
        for mois, vals in moyenne['par_mois'].items():
            if vals['salaire']:
                print(f"    {mois}: salaire {vals['salaire']:.2f}€ "
                      f"- dépenses {vals['depenses']:.2f}€ "
                      f"= solde {vals['solde']:.2f}€")
 
    # 4단계: 그래프 생성
    print("\n Création des graphiques...")
    vis = Visualiseur()
 
    buf_camembert_par_mois = vis.graphique_camembert_par_mois(  
        categories_par_mois,
        "Répartition des dépenses par mois"
    )
    buf_barres = vis.graphique_barres_budget(
        comparaison, "Budget prévu vs Dépenses réelles"
    )
    buf_tendances = vis.graphique_tendances(
        tendances, "Tendances des dépenses par catégorie"
    )
    buf_epargne = vis.graphique_epargne(
        epargne, f"Progression vers l'objectif ({OBJECTIF_EPARGNE:.0f}€)"
    )
 
    # 5단계: PDF 생성
    print("\n Génération du rapport PDF...")
    gen = GenerateurPDF(CHEMIN_PDF)
    gen.generer(
        categories, moyenne, comparaison, epargne,
        buf_camembert_par_mois,   
        buf_barres, buf_tendances, buf_epargne
    )
 
    print("\n" + "=" * 55)
    print(f"   Terminé ! Rapport : {CHEMIN_PDF}")
    print("=" * 55)