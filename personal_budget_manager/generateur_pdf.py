from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage,
                                 HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

# Classe permettant de générer un rapport PDF de gestion de budget.
class GenerateurPDF:

    def __init__(self, chemin_sortie="rapport_budget.pdf"):
        self.chemin_sortie = chemin_sortie # Chemin de sortie du fichier PDF
        self.styles = getSampleStyleSheet() # Styles par défaut fournis par reportlab
        self._creer_styles() # Création des styles personnalisés
    
    # Crée et configure les styles personnalisés utilisés dans le PDF.
    def _creer_styles(self):
        """
        Crée et configure les styles personnalisés utilisés dans le PDF.

        Cette méthode permet de définir l'apparence des différents éléments du rapport :
        - le titre principal
         les titres de sections
        - le texte courant
        - les messages de succès (économie)
        - les messages d'alerte (dépassement)
        
        """
        
        self.style_titre = ParagraphStyle(  # Style du titre principal (grand, centré, en gras)
            'MonTitre', parent=self.styles['Title'],
            fontSize=22, textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold'
        )

        # Style des titres de sections (plus petits que le titre principal)
        self.style_section = ParagraphStyle(
            'MaSection', parent=self.styles['Heading2'],
            fontSize=13, textColor=colors.HexColor('#2980b9'),
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'
        )

        # Style du texte normal
        self.style_corps = ParagraphStyle(
            'MonCorps', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#34495e'),
            spaceAfter=4, leading=14
        )

        # Style pour les messages positifs (économie)
        self.style_succes = ParagraphStyle(
            'Succes', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#27ae60'),
            spaceAfter=4, fontName='Helvetica-Bold'
        )

        # Style utilisé pour les messages négatifs (dépassement de budget)
        self.style_alerte = ParagraphStyle(
            'Alerte', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#e74c3c'),
            spaceAfter=4, fontName='Helvetica-Bold'
        )

    # Convertit une image en buffer en objet affichable dans le PDF.
    def _ajouter_image(self, buf_image, largeur=14*cm, hauteur=8*cm):
        buf_image.seek(0)
        return RLImage(buf_image, width=largeur, height=hauteur)
    
    # Fonction principale pour générer le rapport PDF.
    def generer(self, categories, moyenne_mensuelle, comparaison,
                epargne, buf_camembert_par_mois, buf_barres,
                buf_tendances, buf_epargne):
        """
        Paramètres :
            categories             : résultat de l'analyse des catégories
            moyenne_mensuelle      : moyenne des dépenses par mois
            comparaison            : comparaison budget vs dépenses
            epargne                : informations sur l'épargne
            buf_camembert_par_mois : graphique camembert mensuel
            buf_barres             : graphique en barres du budget
            buf_tendances          : graphique des tendances
            buf_epargne            : graphique de l'épargne

        """
        # Création du document PDF avec marges
        doc = SimpleDocTemplate(
            self.chemin_sortie, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2*cm
        )

        contenu = []

        # ===== Titre =====
        contenu.append(Paragraph("Rapport de Gestion Budget", self.style_titre))
        # Sous-titre
        contenu.append(Paragraph(
            "Analyse complète de vos dépenses personnelles",
            ParagraphStyle('sous_titre', parent=self.styles['Normal'],
                           fontSize=11, textColor=colors.HexColor('#7f8c8d'),
                           alignment=TA_CENTER, spaceAfter=15)
        ))
        # Ligne de séparation
        contenu.append(HRFlowable(width="100%", thickness=1.5,
                                   color=colors.HexColor('#3498db'), spaceAfter=15))

        # ---- Section 1: Répartition des dépenses mensuelles par catégorie ----
        contenu.append(Paragraph("1. Répartition des dépenses mensuelles par catégorie",
                                  self.style_section))
        contenu.append(Spacer(1, 10))

        # Calcul de la hauteur du graphique selon le nombre de mois
        nb_mois   = len(moyenne_mensuelle['par_mois'])
        nb_lignes = max(1, (nb_mois + 2) // 3)   #  Par lignes de trois
        hauteur_camembert = min(20, nb_lignes * 7) * cm
        # Ajout du graphique
        contenu.append(self._ajouter_image(buf_camembert_par_mois, 16*cm, hauteur_camembert))
        contenu.append(Spacer(1, 15))

        # Tableau récapitulatif des dépenses par catégorie
        tableau_data = [['Catégories', 'Dépenses cumulées', 'Répartition (%)']]
        for cat, vals in categories.items():
            tableau_data.append([cat, f"{vals['total']:.2f} €", f"{vals['pourcentage']} %"])

        tableau = Table(tableau_data, colWidths=[7*cm, 5*cm, 4*cm])
        # Style du tableau
        tableau.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#2980b9')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  10),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1),
             [colors.HexColor('#ecf0f1'), colors.white]),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        contenu.append(tableau)
        contenu.append(Spacer(1, 10))

        # ---- Section 2: Moyenne mensuelle des dépenses ----
        contenu.append(Paragraph("2. Moyenne mensuelle des dépenses",
                                  self.style_section))
        contenu.append(Paragraph(
            f"Dépense mensuelle moyenne : <b>{moyenne_mensuelle['moyenne']:.2f} €</b>",
            self.style_corps
        ))

        # Récapitulatif des dépenses dans le tableau avec le solde restant
        a_salaire = moyenne_mensuelle.get('a_un_revenu', False)
         # Création du tableau avec 4 colonnes (mois, dépenses, salaire, solde)
        mois_data = [['Mois', 'Dépenses', 'Salaire', 'Solde restant']]

        # Parcours des données mensuelles
        for mois, vals in moyenne_mensuelle['par_mois'].items():
            # Affichage du salaire (si présent), sinon tiret
            salaire = f"{vals['salaire']:.2f} €" if vals['salaire'] else "—"
            # Affichage du solde restant (si présent), sinon tiret
            solde   = f"{vals['solde']:.2f} €"   if vals['solde']   else "—"
            # Si le solde est négatif, on l'affiche en rouge pour signaler un problème
            if vals['solde'] is not None and vals['solde'] < 0:
                solde = f"<font color='red'>{vals['solde']:.2f} €</font>"
            # Style centré pour la cellule du solde
            style_solde = ParagraphStyle('solde', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.black)
            # Ajout d'une ligne au tableau
            mois_data.append([
                mois,
                f"{vals['depenses']:.2f} €",
                salaire,
                Paragraph(solde, style_solde)
            ])
        col_widths = [5*cm, 4*cm, 4*cm, 4*cm]

        # Création du tableau PDF avec les données construites
        tableau_mois = Table(mois_data, colWidths=col_widths)
        tableau_mois.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#27ae60')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1),
             [colors.HexColor('#eafaf1'), colors.white]),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        # Ajout du tableau au document PDF
        contenu.append(tableau_mois)
        contenu.append(Spacer(1, 10))

        # ---- Section 3 : Vérification du respect du budget ----
        contenu.append(Paragraph("3. Respect du budget par catégorie", self.style_section))
        contenu.append(self._ajouter_image(buf_barres, 16*cm, 7.5*cm))
        contenu.append(Spacer(1, 8))

        # Parcourt chaque catégorie pour afficher un résumé textuel
        for cat, vals in comparaison.items():
            # Si les dépenses sont inférieures au budget, il s'agit d'une économie
            if vals['statut'] == 'économie':
                msg = (f"<b>{cat}</b> : Budget {vals['budget_total']:.2f}€ → "
                       f"Dépensé {vals['depense_totale']:.2f}€ → "
                       f"<font color='green'>Économie de {vals['ecart']:.2f}€</font>")
            # Sinon, cela signifie que le budget a été dépassé
            else:
                msg = (f"<b>{cat}</b> : Budget {vals['budget_total']:.2f}€ → "
                       f"Dépensé {vals['depense_totale']:.2f}€ → "
                       f"<font color='red'>Dépassement de {vals['ecart']:.2f}€</font>")
            contenu.append(Paragraph(msg, self.style_corps))

        contenu.append(Spacer(1, 10))

        # ---- Section 4 : Suivi de l'épargne ----
        contenu.append(Paragraph("4. Épargne accumulée", self.style_section))
        contenu.append(self._ajouter_image(buf_epargne, 14*cm, 4*cm))
        contenu.append(Spacer(1, 6))

        # Affiche la situation actuelle de l'épargne par rapport à l'objectif fixé
        contenu.append(Paragraph(
            f"Épargne actuelle : <b>{epargne['epargne_accumulee']:.2f}€</b> "
            f"sur un objectif de <b>{epargne['objectif']:.2f}€</b> "
            f"({epargne['pourcentage_atteint']}% atteint)",
            self.style_corps
        ))
        # Affiche la situation actuelle de l'épargne par rapport à l'objectif fixé
        if epargne['restant'] > 0:
            contenu.append(Paragraph(
                f"Il vous reste <b>{epargne['restant']:.2f}€</b> à économiser.",
                self.style_corps
            ))
            
        # Ajoute un espace avant la section suivante
        else:
            contenu.append(Paragraph(
                "Félicitations ! Vous avez atteint votre objectif d'épargne !",
                self.style_succes
            ))

        contenu.append(Spacer(1, 10))

        # ---- Section 5 : Analyse des tendances ----
        contenu.append(Paragraph("5. Tendances des dépenses", self.style_section))
        contenu.append(self._ajouter_image(buf_tendances, 16*cm, 7.5*cm))

        # Génère et enregistre le document PDF final
        doc.build(contenu)
        print(f"Rapport PDF généré : {self.chemin_sortie}")