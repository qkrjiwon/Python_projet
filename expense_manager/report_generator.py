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
    # 커스텀 스타일 정의
    # ReportLab 기본 스타일을 확장하여
    # 보고서에 맞는 디자인 적용
    # ─────────────────────────────────────────────
    def _setup_custom_styles(self):
        """PDF 커스텀 스타일 설정"""

        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#2980B9'),
            spaceBefore=15,
            spaceAfter=8,
            borderPad=4
        ))

        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#7F8C8D'),
            spaceBefore=8,
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            name='HighlightGreen',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#27AE60'),
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            name='HighlightRed',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#E74C3C'),
            spaceAfter=4
        ))

    # ─────────────────────────────────────────────
    # PDF 생성 메인 함수
    # 모든 섹션을 순서대로 조합하여 PDF 생성
    # ─────────────────────────────────────────────
    def generate_pdf(self,
                     category_ratios: pd.DataFrame,
                     budget_eval: pd.DataFrame,
                     savings_data: dict,
                     monthly_stats: dict,
                     selected_month: str = None) -> bytes:
        """
        전체 분석 보고서를 PDF로 생성

        Returns:
            bytes : PDF 파일 바이트 데이터
                    → Streamlit에서 다운로드 버튼에 직접 사용 가능
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

        # 보고서 구성 요소 리스트
        story = []

        # ── 표지 섹션 ──
        story += self._build_cover(selected_month)

        # ── 요약 섹션 ──
        story += self._build_summary(savings_data, monthly_stats)

        # ── 카테고리 비율 섹션 ──
        story += self._build_category_section(category_ratios)

        # ── 예산 평가 섹션 ──
        story += self._build_budget_section(budget_eval)

        # ── 저축 진행 섹션 ──
        story += self._build_savings_section(savings_data)

        # PDF 빌드
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_cover(self, selected_month: str = None) -> list:
        """보고서 표지 생성"""
        elements = []

        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(
            "📊 Rapport Financier Personnel",
            self.styles['CustomTitle']
        ))

        # 기간 표시
        period = selected_month if selected_month else "Toute la période"
        elements.append(Paragraph(
            f"Période analysée : <b>{period}</b>",
            self.styles['SubHeader']
        ))

        # 생성 날짜
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
        """핵심 요약 섹션 생성"""
        elements = []

        elements.append(Paragraph(
            "🔍 Résumé Exécutif",
            self.styles['SectionHeader']
        ))

        # 핵심 지표 테이블
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
            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            # 데이터 행 스타일
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

        # 저축 메시지
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
        """카테고리별 지출 비율 섹션"""
        elements = []

        elements.append(Paragraph(
            "📂 Répartition des Dépenses par Catégorie",
            self.styles['SectionHeader']
        ))

        # 테이블 헤더
        table_data = [['Catégorie', 'Montant (€)', 'Pourcentage (%)']]

        for _, row in category_ratios.iterrows():
            # 비율에 따라 시각적 바 생성
            bar_length = int(row['pourcentage'] / 5)
            bar = '█' * bar_length

            table_data.append([
                row['catégorie'],
                f"{row['total']:.2f} €",
                f"{row['pourcentage']:.1f}%  {bar}"
            ])

        # 합계 행 추가
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
            # 합계 행 강조
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
        """예산 평가 섹션"""
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

        # 행별 색상 조건부 적용
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1),)
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]

        # 초과/절약에 따라 행 색상 변경
        for i, (_, row) in enumerate(budget_eval.iterrows(), start=1):
            if row['différence (€)'] < 0:
                # 예산 초과 → 연한 빨강
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i),
                     colors.HexColor('#FADBD8'))
                )
            else:
                # 예산 내 → 연한 초록
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i),
                     colors.HexColor('#D5F5E3'))
                )

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        return elements

    def _build_savings_section(self, savings_data: dict) -> list:
        """저축 진행 섹션"""
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

        # 월별 저축이 음수(지출 초과)인 경우 빨간색 표시
        for i, (_, row) in enumerate(savings_df.iterrows(), start=1):
            if row['épargne_mois'] < 0:
                style_commands.append(
                    ('TEXTCOLOR', (2, i), (2, i),
                     colors.HexColor('#E74C3C'))
                )

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))

        # 최종 메시지
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
    # CSV 생성
    # 여러 DataFrame을 하나의 ZIP으로 묶어서 반환
    # ─────────────────────────────────────────────
    def generate_csv(self,
                     category_ratios: pd.DataFrame,
                     budget_eval: pd.DataFrame,
                     savings_data: dict,
                     transactions: pd.DataFrame) -> bytes:
        """
        분석 데이터를 CSV 파일들로 생성 후 ZIP으로 압축

        Returns:
            bytes : ZIP 파일 바이트 데이터
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w',
                             zipfile.ZIP_DEFLATED) as zip_file:

            # 1. 카테고리 비율 CSV
            csv1 = io.StringIO()
            category_ratios.to_csv(csv1, index=False, sep=';',
                                    encoding='utf-8-sig')
            zip_file.writestr(
                'rapport_categories.csv',
                csv1.getvalue()
            )

            # 2. 예산 평가 CSV
            csv2 = io.StringIO()
            budget_eval.to_csv(csv2, index=False, sep=';',
                                encoding='utf-8-sig')
            zip_file.writestr(
                'rapport_budget.csv',
                csv2.getvalue()
            )

            # 3. 저축 추이 CSV
            csv3 = io.StringIO()
            savings_data['savings_df'].to_csv(
                csv3, index=False, sep=';', encoding='utf-8-sig'
            )
            zip_file.writestr(
                'rapport_epargne.csv',
                csv3.getvalue()
            )

            # 4. 전체 거래 내역 CSV
            csv4 = io.StringIO()
            transactions.to_csv(csv4, index=False, sep=';',
                                  encoding='utf-8-sig')
            zip_file.writestr(
                'transactions_completes.csv',
                csv4.getvalue()
            )

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
