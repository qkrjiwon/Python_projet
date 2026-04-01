from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage,
                                 HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER


class GenerateurPDF:
    """
    사용법:
        gen = GenerateurPDF("rapport.pdf")
        gen.generer(...)
    """

    def __init__(self, chemin_sortie="rapport_budget.pdf"):
        self.chemin_sortie = chemin_sortie
        self.styles        = getSampleStyleSheet()
        self._creer_styles()

    def _creer_styles(self):
        self.style_titre = ParagraphStyle(
            'MonTitre', parent=self.styles['Title'],
            fontSize=22, textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold'
        )
        self.style_section = ParagraphStyle(
            'MaSection', parent=self.styles['Heading2'],
            fontSize=13, textColor=colors.HexColor('#2980b9'),
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'
        )
        self.style_corps = ParagraphStyle(
            'MonCorps', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#34495e'),
            spaceAfter=4, leading=14
        )
        self.style_succes = ParagraphStyle(
            'Succes', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#27ae60'),
            spaceAfter=4, fontName='Helvetica-Bold'
        )
        self.style_alerte = ParagraphStyle(
            'Alerte', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#e74c3c'),
            spaceAfter=4, fontName='Helvetica-Bold'
        )

    def _ajouter_image(self, buf_image, largeur=14*cm, hauteur=8*cm):
        buf_image.seek(0)
        return RLImage(buf_image, width=largeur, height=hauteur)

    def generer(self, categories, moyenne_mensuelle, comparaison,
                epargne, buf_camembert_par_mois, buf_barres,
                buf_tendances, buf_epargne):
        """
        PDF 보고서를 생성하는 메인 함수

        매개변수:
            categories             = analyser_categories() 결과
            moyenne_mensuelle      = calculer_moyenne_mensuelle() 결과
            comparaison            = comparer_budget() 결과
            epargne                = calculer_epargne() 결과
            buf_camembert_par_mois = graphique_camembert_par_mois() 이미지 ✅
            buf_barres             = graphique_barres_budget() 이미지
            buf_tendances          = graphique_tendances() 이미지
            buf_epargne            = graphique_epargne() 이미지
        """
        doc = SimpleDocTemplate(
            self.chemin_sortie, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2*cm
        )

        contenu = []

        # ---- 제목 ----
        contenu.append(Paragraph("Rapport de Gestion Budget", self.style_titre))
        contenu.append(Paragraph(
            "Analyse complète de vos dépenses personnelles",
            ParagraphStyle('sous_titre', parent=self.styles['Normal'],
                           fontSize=11, textColor=colors.HexColor('#7f8c8d'),
                           alignment=TA_CENTER, spaceAfter=15)
        ))
        contenu.append(HRFlowable(width="100%", thickness=1.5,
                                   color=colors.HexColor('#3498db'), spaceAfter=15))

        # ---- 섹션 1: 월별 파이 차트 ✅ ----
        contenu.append(Paragraph("1. Répartition des dépenses mensuelles par catégorie",
                                  self.style_section))
        contenu.append(Spacer(1, 10))

        # 달 수에 따라 이미지 높이 자동 조정
        nb_mois   = len(moyenne_mensuelle['par_mois'])
        nb_lignes = max(1, (nb_mois + 2) // 3)   # 3개씩 한 줄
        hauteur_camembert = min(20, nb_lignes * 7) * cm

        contenu.append(self._ajouter_image(buf_camembert_par_mois, 16*cm, hauteur_camembert))
        contenu.append(Spacer(1, 15))

        # 전체 합산 요약 표
        tableau_data = [['Catégories', 'Dépenses cumulées', 'Répartition (%)']]
        for cat, vals in categories.items():
            tableau_data.append([cat, f"{vals['total']:.2f} €", f"{vals['pourcentage']} %"])

        tableau = Table(tableau_data, colWidths=[7*cm, 5*cm, 4*cm])
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

        # ---- 섹션 2: 월별 평균 + 월급/잔액 ✅ ----
        contenu.append(Paragraph("2. Moyenne mensuelle des dépenses",
                                  self.style_section))
        contenu.append(Paragraph(
            f"Dépense mensuelle moyenne : <b>{moyenne_mensuelle['moyenne']:.2f} €</b>",
            self.style_corps
        ))

        # 월급 데이터가 있으면 열을 더 추가
        a_salaire = moyenne_mensuelle.get('a_un_salaire', False)

        if a_salaire:
            mois_data = [['Mois', 'Dépenses', 'Salaire', 'Solde restant']]
            for mois, vals in moyenne_mensuelle['par_mois'].items():
                salaire = f"{vals['salaire']:.2f} €" if vals['salaire'] else "—"
                solde   = f"{vals['solde']:.2f} €"   if vals['solde']   else "—"
                # 잔액이 마이너스면 빨간색
                if vals['solde'] is not None and vals['solde'] < 0:
                    solde = f"<font color='red'>{vals['solde']:.2f} €</font>"
                style_solde = ParagraphStyle('solde', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.black)
                mois_data.append([
                    mois,
                    f"{vals['depenses']:.2f} €",
                    salaire,
                    Paragraph(solde, style_solde)
                ])
            col_widths = [5*cm, 4*cm, 4*cm, 4*cm]
        else:
            mois_data = [['Mois', 'Dépenses totales']]
            for mois, vals in moyenne_mensuelle['par_mois'].items():
                mois_data.append([mois, f"{vals['depenses']:.2f} €"])
            col_widths = [9*cm, 7*cm]

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
        contenu.append(tableau_mois)
        contenu.append(Spacer(1, 10))

        # ---- 섹션 3: 예산 준수 여부 ----
        contenu.append(Paragraph("3. Respect du budget par catégorie", self.style_section))
        contenu.append(self._ajouter_image(buf_barres, 16*cm, 7.5*cm))
        contenu.append(Spacer(1, 8))

        for cat, vals in comparaison.items():
            if vals['statut'] == 'économie':
                msg = (f"<b>{cat}</b> : Budget {vals['budget_total']:.2f}€ → "
                       f"Dépensé {vals['depense_totale']:.2f}€ → "
                       f"<font color='green'>Économie de {vals['ecart']:.2f}€</font>")
            else:
                msg = (f"<b>{cat}</b> : Budget {vals['budget_total']:.2f}€ → "
                       f"Dépensé {vals['depense_totale']:.2f}€ → "
                       f"<font color='red'>Dépassement de {vals['ecart']:.2f}€</font>")
            contenu.append(Paragraph(msg, self.style_corps))

        contenu.append(Spacer(1, 10))

        # ---- 섹션 4: 저축 달성률 ----
        contenu.append(Paragraph("4. Épargne accumulée", self.style_section))
        contenu.append(self._ajouter_image(buf_epargne, 14*cm, 4*cm))
        contenu.append(Spacer(1, 6))

        contenu.append(Paragraph(
            f"Épargne actuelle : <b>{epargne['epargne_accumulee']:.2f}€</b> "
            f"sur un objectif de <b>{epargne['objectif']:.2f}€</b> "
            f"({epargne['pourcentage_atteint']}% atteint)",
            self.style_corps
        ))
        if epargne['restant'] > 0:
            contenu.append(Paragraph(
                f"Il vous reste <b>{epargne['restant']:.2f}€</b> à économiser.",
                self.style_corps
            ))
        else:
            contenu.append(Paragraph(
                "Félicitations ! Vous avez atteint votre objectif d'épargne !",
                self.style_succes
            ))

        contenu.append(Spacer(1, 10))

        # ---- 섹션 5: 추세 그래프 ----
        contenu.append(Paragraph("5. Tendances des dépenses", self.style_section))
        contenu.append(self._ajouter_image(buf_tendances, 16*cm, 7.5*cm))

        doc.build(contenu)
        print(f"Rapport PDF généré : {self.chemin_sortie}")