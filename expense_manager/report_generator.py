"""
Module de génération de rapports PDF et CSV.
Responsabilité : Exporter toutes les données analysées
en format téléchargeable.
"""

import pandas as pd
import io
import zipfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class ReportGenerator:

    def __init__(self):
        # PDF 스타일 초기화
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    # ─────────────────────────────────────────────
    # Définition des styles personnalisés
    # Extension des styles de base de ReportLab pour le rapport
    # ─────────────────────────────────────────────
    def _setup_custom_styles(self):
        """Configuration des styles personnalisés pour le PDF"""

        # ─────────────────────────────────────────────
        # Vérifie si le style existe déjà avant de l'ajouter
        # Évite les erreurs de conflit lors de ré-initialisations
        # ─────────────────────────────────────────────
        def add_style_safe(style):
            """Ajoute un style uniquement s'il n'existe pas déjà"""
            if style.name not in self.styles:
                self.styles.add(style)

        add_style_safe(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))

        add_style_safe(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#2980B9'),
            spaceBefore=15,
            spaceAfter=8,
            borderPad=4
        ))

        add_style_safe(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#7F8C8D'),
            spaceBefore=8,
            spaceAfter=4
        ))

        add_style_safe(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=4
        ))

        add_style_safe(ParagraphStyle(
            name='HighlightGreen',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#27AE60'),
            spaceAfter=4
        ))

        add_style_safe(ParagraphStyle(
            name='HighlightRed',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#E74C3C'),
            spaceAfter=4
        ))


    # ─────────────────────────────────────────────
    # Fonction principale de génération PDF
    # Combine toutes les sections pour créer le rapport final
    # ─────────────────────────────────────────────
    def generate_pdf(self,
                     category_ratios: pd.DataFrame,
                     budget_eval: pd.DataFrame,
                     savings_data: dict,
                     monthly_stats: dict,
                     selected_month: str = None) -> bytes:
        """
        Génère un rapport d'analyse complet en format PDF.

        Returns:
            bytes : Données binaires du fichier PDF 
                    (utilisables directement pour le bouton de téléchargement Streamlit)
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Liste des éléments constituant le document
        story = []

        # ── Section Page de couverture ──
        story += self._build_cover(selected_month)

        # ── Section Résumé ──
        story += self._build_summary(savings_data, monthly_stats)

        # ── Section Répartition par catégorie ──
        story += self._build_category_section(category_ratios)

        # ── Section Évaluation du budget ──
        story += self._build_budget_section(budget_eval)

        # ── Section Suivi de l'épargne ──
        story += self._build_savings_section(savings_data)

        # Construction du PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_cover(self, selected_month: str = None) -> list:
        """Génère la couverture du rapport"""
        elements = []

        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(
            "📊 Rapport Financier Personnel",
            self.styles['CustomTitle']
        ))

        # Affichage de la période
        period = selected_month if selected_month else "Toute la période"
        elements.append(Paragraph(
            f"Période analysée : <b>{period}</b>",
            self.styles['SubHeader']
        ))

        # Date de génération
        elements.append(Paragraph(
            f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['SubHeader']
        ))

        elements.append(Spacer(1, 0.5*cm))
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor('#2980B9')
        ))
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_summary(self, savings_data: dict,
                        monthly_stats: dict) -> list:
        """Génère la section Résumé Exécutif"""
        elements = []

        elements.append(Paragraph(
            "🔍 Résumé Exécutif",
            self.styles['SectionHeader']
        ))

        # Tableau des indicateurs clés
        avg = monthly_stats.get('avg_monthly_total', 0)
        total_saved = savings_data.get('total_saved', 0)
        remaining = savings_data.get('remaining', 0)
        progress = savings_data.get('progress_pct', 0)

        summary_data = [
            ['Indicateur', 'Valeur'],
            ['Dépenses moyennes mensuelles', f"{avg:.2f} €"],
            ['Épargne cumulée totale', f"{total_saved:.2f} €"],
            ['Objectif annuel d\'épargne', f"{savings_data.get('goal', 0):.2f} €"],
            ['Reste à épargner', f"{remaining:.2f} €"],
            ['Progression vers l\'objectif', f"{progress:.1f} %"],
        ]

        table = Table(summary_data, colWidths=[10*cm, 6*cm])
        table.setStyle(TableStyle([
            # Style de l'en-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            # Style des lignes de données
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#EBF5FB')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))

        # Message sur l'épargne
        if remaining > 0:
            msg = f"💡 Il vous reste <b>{remaining:.2f} €</b> à épargner pour atteindre votre objectif."
            elements.append(Paragraph(msg, self.styles['HighlightRed']))
        else:
            msg = f"🎉 Félicitations ! Vous avez atteint votre objectif d'épargne !"
            elements.append(Paragraph(msg, self.styles['HighlightGreen']))

        elements.append(Spacer(1, 0.3*cm))
        return elements

    def _build_category_section(self,
                                  category_ratios: pd.DataFrame) -> list:
        """Génère la section des dépenses par catégorie"""
        elements = []

        elements.append(Paragraph(
            "📂 Répartition des Dépenses par Catégorie",
            self.styles['SectionHeader']
        ))

        # En-tête du tableau
        table_data = [['Catégorie', 'Montant (€)', 'Pourcentage (%)']]

        for _, row in category_ratios.iterrows():
            # Création d'une barre visuelle basée sur le pourcentage
            bar_length = int(row['pourcentage'] / 5)
            bar = '█' * bar_length

            table_data.append([
                row['catégorie'],
                f"{row['total']:.2f} €",
                f"{row['pourcentage']:.1f}%  {bar}"
            ])

        # Ajout d'une ligne de total
        table_data.append([
            'TOTAL',
            f"{category_ratios['total'].sum():.2f} €",
            '100%'
        ])

        table = Table(table_data, colWidths=[6*cm, 4*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            # Accentuation de la ligne Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D5F5E3')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2),
             [colors.white, colors.HexColor('#FDFEFE')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        return elements

    def _build_budget_section(self,
                               budget_eval: pd.DataFrame) -> list:
        """Génère la section d'évaluation du budget"""
        elements = []

        elements.append(Paragraph(
            "💰 Évaluation du Budget",
            self.styles['SectionHeader']
        ))

        table_data = [['Catégorie', 'Budget', 'Réel', 'Différence', 'Statut']]

        for _, row in budget_eval.iterrows():
            table_data.append([
                row['catégorie'],
                f"{row['budget (€)']:.2f} €",
                f"{row['réel (€)']:.2f} €",
                f"{row['différence (€)']:.2f} €",
                row['statut']
            ])

        table = Table(table_data,
                      colWidths=[4.5*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm])

        # Application conditionnelle des couleurs par ligne
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),  # ✅ 수정
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]

        # Changement de couleur selon dépassement ou économie
        for i, (_, row) in enumerate(budget_eval.iterrows(), start=1):
            if row['différence (€)'] < 0:
                # Dépassement de budget → Rouge clair
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i),
                     colors.HexColor('#FADBD8'))
                )
            else:
                # Dans le budget → Vert clair
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i),
                     colors.HexColor('#D5F5E3'))
                )

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        return elements

    def _build_savings_section(self, savings_data: dict) -> list:
        """Génère la section du suivi de l'épargne"""
        elements = []

        elements.append(Paragraph(
            "🏦 Suivi de l'Épargne",
            self.styles['SectionHeader']
        ))

        savings_df = savings_data['savings_df']

        table_data = [['Mois', 'Dépenses (€)',
                        'Épargne du mois (€)', 'Épargne cumulée (€)']]

        for _, row in savings_df.iterrows():
            table_data.append([
                row['mois'],
                f"{row['dépenses']:.2f} €",
                f"{row['épargne_mois']:.2f} €",
                f"{row['épargne_cumulée']:.2f} €"
            ])

        table = Table(table_data,
                      colWidths=[4*cm, 4*cm, 4.5*cm, 4.5*cm])

        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#EBF5FB')]),
        ]

        # Si l'épargne mensuelle est négative (dépenses > revenus), affichage en rouge
        for i, (_, row) in enumerate(savings_df.iterrows(), start=1):
            if row['épargne_mois'] < 0:
                style_commands.append(
                    ('TEXTCOLOR', (2, i), (2, i),
                     colors.HexColor('#E74C3C'))
                )

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))

        # Message de fin
        remaining = savings_data['remaining']
        progress = savings_data['progress_pct']

        elements.append(Paragraph(
            f"📈 Progression : <b>{progress:.1f}%</b> de l'objectif atteint.",
            self.styles['BodyText']
        ))

        if remaining > 0:
            elements.append(Paragraph(
                f"➡️ Il vous reste <b>{remaining:.2f} €</b> "
                f"pour atteindre votre objectif annuel.",
                self.styles['HighlightRed']
            ))
        else:
            elements.append(Paragraph(
                "🎉 Objectif d'épargne annuel atteint !",
                self.styles['HighlightGreen']
            ))

        return elements

    # ─────────────────────────────────────────────
    # Génération CSV
    # Regroupe plusieurs DataFrames dans une archive ZIP
    # ─────────────────────────────────────────────
    def generate_csv(self,
                     category_ratios: pd.DataFrame,
                     budget_eval: pd.DataFrame,
                     savings_data: dict,
                     transactions: pd.DataFrame) -> bytes:
        """
        Génère les données d'analyse en fichiers CSV et les compresse en ZIP.

        Returns:
            bytes : Données binaires du fichier ZIP
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w',
                             zipfile.ZIP_DEFLATED) as zip_file:

            # 1. CSV des ratios par catégorie
            csv1 = io.StringIO()
            category_ratios.to_csv(csv1, index=False, sep=';',
                                    encoding='utf-8-sig')
            zip_file.writestr(
                'rapport_categories.csv',
                csv1.getvalue()
            )

            # 2. CSV de l'évaluation du budget
            csv2 = io.StringIO()
            budget_eval.to_csv(csv2, index=False, sep=';',
                                encoding='utf-8-sig')
            zip_file.writestr(
                'rapport_budget.csv',
                csv2.getvalue()
            )

            # 3. CSV du suivi de l'épargne
            csv3 = io.StringIO()
            savings_data['savings_df'].to_csv(
                csv3, index=False, sep=';', encoding='utf-8-sig'
            )
            zip_file.writestr(
                'rapport_epargne.csv',
                csv3.getvalue()
            )

            # 4. CSV des transactions complètes
            csv4 = io.StringIO()
            transactions.to_csv(csv4, index=False, sep=';',
                                  encoding='utf-8-sig')
            zip_file.writestr(
                'transactions_completes.csv',
                csv4.getvalue()
            )

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
