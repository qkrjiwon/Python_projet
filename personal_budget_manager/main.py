# =============================================================
# Rôle : Point d'entrée du programme — Importe toutes les classes et les exécute dans l'ordre.
# Exécution (dans le terminal VS Code) :
#   python main.py
# =============================================================

# Importation des classes depuis les fichiers du même dossier
from lecteur_csv   import LecteurCSV          # lecteur_csv.py
from analyseur      import AnalyseurDepenses   # analyseur.py
from visualiseur    import Visualiseur         # visualiseur.py
from generateur_pdf import GenerateurPDF       # generateur_pdf.py

# Le nom du fichier où se trouvent les dépenses
CHEMIN_CSV = "transactions.csv"
 
# Définition des budgets mensuels par catégorie
MES_BUDGETS = {
    'Transport':          150,
    'Alimentation':       250,
    'Logement':           750,
    'Shopping':            80,
    'Loisirs':             60,
    'Remboursement prêt': 200,
}

# La somme que tu aimerais mettre de côté
OBJECTIF_EPARGNE = 1500.0
# Le nom du fichier final
CHEMIN_PDF       = "rapport_budget.pdf"
  
# =============================================================
if __name__ == "__main__":
 
    print("=" * 55)
    print("   GESTION BUDGET PERSONNEL - Rapport de dépenses")
    print("=" * 55)
 
    # ÉTAPE 1 : Lecture du fichier CSV
    print("\n Lecture du fichier CSV...")
    lecteur = LecteurCSV(CHEMIN_CSV)
    donnees = lecteur.lire()

    # Si le fichier est vide ou introuvable, on arrête tout proprement
    if donnees is None:
        print("Impossible de lire le fichier. Programme arrêté.")
        exit()
 
    # ÉTAPE 2 : Analyse des données
    print("\n Analyse des données...")
    analyseur = AnalyseurDepenses(donnees)
 
    categories              = analyseur.analyser_categories()
    categories_par_mois     = analyseur.analyser_categories_par_mois()  
    moyenne                 = analyseur.calculer_moyenne_mensuelle()
    comparaison, _          = analyseur.comparer_budget(MES_BUDGETS)
    epargne                 = analyseur.calculer_epargne(MES_BUDGETS, OBJECTIF_EPARGNE)
    tendances               = analyseur.analyser_tendances()
 
    # ÉTAPE 3 : Affichage des résultats dans le terminal
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
 
    # Affichage du salaire et du solde (si disponibles)
    if moyenne.get('a_un_revenu'):
        print("\n  Salaire et solde mensuel :")
        for mois, vals in moyenne['par_mois'].items():
            if vals['salaire']:
                print(f"    {mois}: salaire {vals['salaire']:.2f}€ "
                      f"- dépenses {vals['depenses']:.2f}€ "
                      f"= solde {vals['solde']:.2f}€")
 
    # ÉTAPE 4 : Génération des graphiques
    print("\n Création des graphiques...")
    vis = Visualiseur()

    # On génère chaque graphique
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
 
    # ÉTAPE 5 : Génération du rapport PDF
    print("\n Génération du rapport PDF...")
    gen = GenerateurPDF(CHEMIN_PDF)

    # On donne au générateur toutes les données calculées et tous les graphiques
    gen.generer(
        categories, moyenne, comparaison, epargne,
        buf_camembert_par_mois,   
        buf_barres, buf_tendances, buf_epargne
    )
 
    print("\n" + "=" * 55)
    print(f"   ✅ Terminé ! Le rapport a été généré sous : {CHEMIN_PDF}")
    print("=" * 55)