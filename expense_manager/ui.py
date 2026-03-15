"""
Interface utilisateur Streamlit.
Responsabilité : Afficher tous les composants visuels
et orchestrer les interactions utilisateur.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from data_processor import DataProcessor
from budget_manager import BudgetManager
from visualizer import Visualizer
from report_generator import ReportGenerator


# ─────────────────────────────────────────────
# Liste des catégories (utilisées pour le budget)
# ─────────────────────────────────────────────
CATEGORIES = [
    "Loyer", "Alimentation", "Transport",
    "Shopping", "Loisirs", "Remboursement",
    "Santé", "Abonnements", "Autre"
]


def run_app():
    """
    Fonction principale de l'application Streamlit.
    Rendu de tous les composants de l'interface dans l'ordre.
    """

    # ── Configuration de base de la page ──
    st.set_page_config(
        page_title="Gestionnaire Financier",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ── CSS Personnalisé ──
    st.markdown("""
        <style>
            .main-title {
                font-size: 2.2rem;
                font-weight: 700;
                color: #2C3E50;
                text-align: center;
                margin-bottom: 0.5rem;
            }
            .subtitle {
                font-size: 1rem;
                color: #7F8C8D;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                text-align: center;
            }
            .section-divider {
                border-top: 2px solid #EBF5FB;
                margin: 1.5rem 0;
            }
            .stAlert {
                border-radius: 8px;
            }
        </style>
    """, unsafe_allow_html=True)

    # ── En-tête ──
    st.markdown(
        '<div class="main-title">💰 Gestionnaire de Dépenses Personnelles</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="subtitle">Analysez vos finances, respectez votre budget, atteignez vos objectifs</div>',
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────────────
    # Barre latérale : Import de fichier + Paramètres budget
    # Séparé du contenu principal pour plus de clarté
    # ─────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Configuration")

        # ── 1. Importation de fichier ──
        st.subheader("📁 Importer un relevé bancaire")
        uploaded_file = st.file_uploader(
            "Choisissez un fichier CSV ou Excel",
            type=['csv', 'xlsx', 'xls'],
            help="Formats supportés : CSV (séparateur ; ou ,) et Excel"
        )

        # Bouton de téléchargement du fichier exemple
        sample_csv = _generate_sample_csv()
        st.download_button(
            label="📥 Télécharger un fichier exemple",
            data=sample_csv,
            file_name="exemple_releve_bancaire.csv",
            mime="text/csv",
            help="Téléchargez ce fichier pour tester l'application"
        )

        st.markdown("---")

        # ── 2. Correspondance des colonnes ──
        st.subheader("🗂️ Correspondance des colonnes")
        st.caption("Indiquez quelles colonnes correspondent à quoi")

        col_date = st.text_input(
            "Colonne Date", value="date",
            help="Nom exact de la colonne date dans votre fichier"
        )
        col_amount = st.text_input(
            "Colonne Montant", value="montant",
            help="Nom exact de la colonne montant"
        )
        col_label = st.text_input(
            "Colonne Libellé", value="libellé",
            help="Nom exact de la colonne description"
        )

        st.markdown("---")

        # ── 3. Paramètres du budget ──
        st.subheader("💶 Définir votre budget mensuel")

        savings_goal = st.number_input(
            "🎯 Objectif d'épargne annuel (€)",
            min_value=0.0,
            value=2400.0,
            step=100.0,
            help="Montant total que vous souhaitez épargner sur l'année"
        )

        if savings_goal > 0:
            st.info(
                f"💡 Soit **{savings_goal/12:.2f} €/mois** à mettre de côté"
            )

        st.caption("Budget mensuel par catégorie (€)")

        # Saisie du budget par catégorie
        category_budgets = {}
        for cat in CATEGORIES:
            # Valeurs par défaut
            default_values = {
                "Loyer": 800.0,
                "Alimentation": 400.0,
                "Transport": 150.0,
                "Shopping": 100.0,
                "Loisirs": 100.0,
                "Remboursement": 200.0,
                "Santé": 50.0,
                "Abonnements": 80.0,
                "Autre": 50.0
            }
            category_budgets[cat] = st.number_input(
                f"{cat}",
                min_value=0.0,
                value=default_values.get(cat, 0.0),
                step=10.0,
                key=f"budget_{cat}"
            )

        total_budget = sum(category_budgets.values())
        st.metric(
            "Budget total mensuel",
            f"{total_budget:.2f} €",
            help="Somme de tous vos budgets par catégorie"
        )

    # ─────────────────────────────────────────────
    # Écran principal : S'affiche uniquement si un fichier est importé
    # ─────────────────────────────────────────────
    if uploaded_file is None:
        # Écran d'accueil si pas de fichier
        _show_welcome_screen()
        return

    # ── Traitement des données ──
    # Utilisation de session_state pour éviter de retraiter à chaque interaction
    if 'processed_data' not in st.session_state or \
       st.session_state.get('file_name') != uploaded_file.name:

        with st.spinner("⏳ Traitement des données en cours..."):
            try:
                processor = DataProcessor()

                # Chargement du fichier
                raw_df = processor.load_file(uploaded_file)

                # Normalisation des colonnes
                df = processor.normalize_columns(
                    raw_df,
                    date_col=col_date,
                    amount_col=col_amount,
                    label_col=col_label
                )

                # Classification des catégories
                df = processor.categorize_transactions(df)

                # Calcul des statistiques mensuelles
                monthly_stats = processor.compute_monthly_stats(df)

                # Sauvegarde en session
                st.session_state['processed_data'] = df
                st.session_state['monthly_stats'] = monthly_stats
                st.session_state['file_name'] = uploaded_file.name

                st.success(
                    f"✅ {len(df)} transactions chargées avec succès !"
                )

            except Exception as e:
                st.error(f"❌ Erreur lors du traitement : {str(e)}")
                st.stop()

    # ── Récupération des données depuis la session ──
    df = st.session_state['processed_data']
    monthly_stats = st.session_state['monthly_stats']

    # ── Initialisation des modules ──
    budget_manager = BudgetManager()
    visualizer = Visualizer()
    report_gen = ReportGenerator()
    processor = DataProcessor()
    processor.clean_data = df

    # Configuration du budget
    budget_manager.set_budget(category_budgets, savings_goal)

    # ─────────────────────────────────────────────
    # Organisation des onglets (Tabs)
    # ─────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vue d'ensemble",
        "💶 Budget",
        "🏦 Épargne",
        "📈 Tendances",
        "📄 Rapport"
    ])

    # ════════════════════════════════════════════
    # TAB 1 : VUE D'ENSEMBLE
    # ════════════════════════════════════════════
    with tab1:
        st.subheader("📊 Vue d'ensemble des dépenses")

        # ── Filtre de sélection du mois ──
        available_months = df['mois_label'].unique().tolist()
        selected_month = st.selectbox(
            "🗓️ Sélectionner un mois",
            options=["Tous les mois"] + available_months,
            index=0
        )

        month_filter = None if selected_month == "Tous les mois" \
            else selected_month

        # ── Calcul de la répartition par catégorie ──
        category_ratios = processor.compute_category_ratios(
            df, selected_month=month_filter
        )

        # ── Indicateurs clés (Top 3) ──
        col1, col2, col3 = st.columns(3)

        # Total dépenses
        total_expenses = df[df['est_dépense']]['montant_abs'].sum()
        with col1:
            st.metric(
                label="💸 Total des dépenses",
                value=f"{total_expenses:.2f} €",
                help="Total de toutes les dépenses sur la période"
            )

        # Moyenne mensuelle
        avg_monthly = monthly_stats['avg_monthly_total']
        with col2:
            st.metric(
                label="📅 Moyenne mensuelle",
                value=f"{avg_monthly:.2f} €",
                help="Moyenne des dépenses par mois"
            )

        # Catégorie principale (plus grosse dépense)
        top_category = category_ratios.iloc[0]['catégorie'] \
            if not category_ratios.empty else "N/A"
        top_amount = category_ratios.iloc[0]['total'] \
            if not category_ratios.empty else 0
        with col3:
            st.metric(
                label="🏆 Catégorie principale",
                value=top_category,
                delta=f"{top_amount:.2f} €",
                delta_color="off"
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Graphique Circulaire + Table des catégories ──
        col_left, col_right = st.columns([1.2, 0.8])

        with col_left:
            title = f"Répartition - {selected_month}" \
                if month_filter else "Répartition globale"
            fig_pie = visualizer.plot_pie_chart(category_ratios, title=title)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            st.subheader("📋 Détail par catégorie")
            # Affichage du tableau (sans index)
            display_df = category_ratios[
                ['catégorie', 'total', 'pourcentage']
            ].copy()
            display_df.columns = ['Catégorie', 'Montant (€)', '%']
            display_df['Montant (€)'] = display_df['Montant (€)'].map(
                '{:.2f}'.format
            )
            display_df['%'] = display_df['%'].map('{:.1f}%'.format)
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Table des transactions ──
        with st.expander("🔍 Voir toutes les transactions", expanded=False):
            # Fonction de modification manuelle des catégories
            st.caption(
                "💡 Vous pouvez modifier manuellement les catégories"
            )

            display_transactions = df[[
                'date', 'libellé', 'montant', 'catégorie'
            ]].copy()
            display_transactions['date'] = \
                display_transactions['date'].dt.strftime('%d/%m/%Y')

            # Éditeur de données pour modifier les catégories en direct
            edited_df = st.data_editor(
                display_transactions,
                column_config={
                    "catégorie": st.column_config.SelectboxColumn(
                        "Catégorie",
                        options=CATEGORIES,
                        required=True
                    ),
                    "date": st.column_config.TextColumn("Date"),
                    "libellé": st.column_config.TextColumn("Libellé"),
                    "montant": st.column_config.NumberColumn(
                        "Montant (€)",
                        format="%.2f €"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            # Application des modifications
            if st.button("✅ Appliquer les modifications"):
                df['catégorie'] = edited_df['catégorie'].values
                st.session_state['processed_data'] = df
                st.success("Modifications appliquées !")
                st.rerun()

    # ════════════════════════════════════════════
    # TAB 2 : GESTION DU BUDGET
    # ════════════════════════════════════════════
    with tab2:
        st.subheader("💶 Évaluation du Budget Mensuel")

        # Sélection du mois
        selected_month_budget = st.selectbox(
            "🗓️ Choisir le mois à évaluer",
            options=available_months,
            index=len(available_months) - 1,  # Par défaut : le mois le plus récent
            key="budget_month_select"
        )

        # Calcul des dépenses réelles pour le mois choisi
        month_expenses = df[
            (df['est_dépense']) &
            (df['mois_label'] == selected_month_budget)
        ]

        actual_by_category = (
            month_expenses
            .groupby('catégorie')['montant_abs']
            .sum()
            .to_dict()
        )

        # Évaluation budgétaire
        budget_eval = budget_manager.evaluate_budget(
            actual_by_category,
            month_label=selected_month_budget
        )

        # ── Indicateurs de résumé ──
        col1, col2, col3 = st.columns(3)

        total_budget = sum(category_budgets.values())
        total_actual = sum(actual_by_category.values())
        total_diff = total_budget - total_actual

        with col1:
            st.metric(
                "Budget total",
                f"{total_budget:.2f} €"
            )
        with col2:
            st.metric(
                "Dépenses réelles",
                f"{total_actual:.2f} €",
                delta=f"{-total_actual + total_budget:.2f} €",
                delta_color="normal"
            )
        with col3:
            status = "✅ Sous budget" if total_diff >= 0 else "❌ Dépassement"
            st.metric(
                "Solde budgétaire",
                f"{total_diff:.2f} €",
                delta=status,
                delta_color="off"
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Graphique de comparaison budget ──
        fig_budget = visualizer.plot_budget_comparison(
            budget_eval,
            title=f"Budget vs Réel - {selected_month_budget}"
        )
        st.plotly_chart(fig_budget, use_container_width=True)

        # ── Tableau d'évaluation détaillée ──
        st.subheader("📋 Détail par catégorie")
        st.dataframe(
            budget_eval,
            use_container_width=True,
            hide_index=True,
            column_config={
                "budget (€)": st.column_config.NumberColumn(format="%.2f €"),
                "réel (€)": st.column_config.NumberColumn(format="%.2f €"),
                "différence (€)": st.column_config.NumberColumn(
                    format="%.2f €"
                ),
                "utilisé (%)": st.column_config.ProgressColumn(
                    "Utilisé (%)",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%"
                )
            }
        )

    # ════════════════════════════════════════════
    # TAB 3 : SUIVI DE L'ÉPARGNE
    # ════════════════════════════════════════════
    with tab3:
        st.subheader("🏦 Suivi de l'Épargne")

        # Calcul de la progression de l'épargne
        savings_data = budget_manager.compute_savings_progress(
            monthly_stats['monthly_totals']
        )

        # ── Indicateurs clés d'épargne ──
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🎯 Objectif annuel",
                f"{savings_data['goal']:.2f} €"
            )
        with col2:
            st.metric(
                "💰 Épargne cumulée",
                f"{savings_data['total_saved']:.2f} €"
            )
        with col3:
            st.metric(
                "📅 Objectif mensuel",
                f"{savings_data['monthly_goal']:.2f} €"
            )
        with col4:
            remaining = savings_data['remaining']
            st.metric(
                "⏳ Reste à épargner",
                f"{max(remaining, 0):.2f} €",
                delta="Objectif atteint ! 🎉" if remaining <= 0 else None
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Message d'état de l'épargne ──
        remaining = savings_data['remaining']
        progress = savings_data['progress_pct']

        if remaining > 0:
            st.warning(
                f"💡 Il vous reste **{remaining:.2f} €** à épargner "
                f"pour atteindre votre objectif annuel de "
                f"**{savings_data['goal']:.2f} €**"
            )
        else:
            st.success(
                f"🎉 Félicitations ! Vous avez atteint votre objectif "
                f"d'épargne annuel de **{savings_data['goal']:.2f} €** !"
            )

        # Barre de progression (sécurisée entre 0.0 et 1.0)
        st.progress(
            max(0.0, min(progress / 100, 1.0)),  # Contraindre la valeur dans [0,0 ; 1,0]
            text=f"Progression : {progress:.1f}%"
        )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Jauge + Graphique d'aire cumulée ──
        col_left, col_right = st.columns([0.4, 0.6])

        with col_left:
            fig_gauge = visualizer.plot_savings_gauge(savings_data)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_right:
            fig_savings = visualizer.plot_cumulative_savings(
                savings_data['savings_df']
            )
            st.plotly_chart(fig_savings, use_container_width=True)

        # ── Tableau mensuel de l'épargne ──
        st.subheader("📋 Détail mensuel de l'épargne")
        st.dataframe(
            savings_data['savings_df'],
            use_container_width=True,
            hide_index=True,
            column_config={
                "dépenses": st.column_config.NumberColumn(
                    "Dépenses (€)", format="%.2f €"
                ),
                "épargne_mois": st.column_config.NumberColumn(
                    "Épargne du mois (€)", format="%.2f €"
                ),
                "épargne_cumulée": st.column_config.NumberColumn(
                    "Épargne cumulée (€)", format="%.2f €"
                )
            }
        )

    # ════════════════════════════════════════════
    # TAB 4 : TENDANCES
    # ════════════════════════════════════════════
    with tab4:
        st.subheader("📈 Tendances des Dépenses")

        # ── Filtre par catégorie ──
        all_categories = df['catégorie'].unique().tolist()
        selected_categories = st.multiselect(
            "Sélectionner les catégories à afficher",
            options=all_categories,
            default=all_categories,
            help="Choisissez une ou plusieurs catégories"
        )

        if selected_categories:
            # Filtrage des catégories sélectionnées
            filtered_monthly = monthly_stats['by_month_category'][
                monthly_stats['by_month_category']['catégorie']
                .isin(selected_categories)
            ]

            # Graphique linéaire des tendances
            fig_trend = visualizer.plot_trend_lines(filtered_monthly)
            st.plotly_chart(fig_trend, use_container_width=True)

            st.markdown('<div class="section-divider"></div>',
                        unsafe_allow_html=True)

            # ── Moyennes mensuelles par catégorie ──
            st.subheader("📊 Moyenne mensuelle par catégorie")
            # Moyenne des dépenses par catégorie choisie
            avg_data = monthly_stats['category_averages']
            avg_filtered = avg_data[
                avg_data.index.isin(selected_categories)
            ].reset_index()
            avg_filtered.columns = ['Catégorie', 'Moyenne mensuelle (€)']
            avg_filtered = avg_filtered.sort_values(
                'Moyenne mensuelle (€)', ascending=False
            )

            col_left, col_right = st.columns([0.6, 0.4])

            with col_left:
                # Graphique en barres horizontales
                import plotly.express as px
                fig_avg = px.bar(
                    avg_filtered,
                    x='Moyenne mensuelle (€)',
                    y='Catégorie',
                    orientation='h',
                    color='Catégorie',
                    title="Moyenne mensuelle par catégorie",
                    text='Moyenne mensuelle (€)'
                )
                fig_avg.update_traces(
                    texttemplate='%{text:.2f}€',
                    textposition='outside'
                )
                fig_avg.update_layout(
                    showlegend=False,
                    height=350,
                    plot_bgcolor='rgba(240,240,240,0.3)'
                )
                st.plotly_chart(fig_avg, use_container_width=True)

            with col_right:
                st.dataframe(
                    avg_filtered,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Moyenne mensuelle (€)": st.column_config.NumberColumn(
                            format="%.2f €"
                        )
                    }
                )

            st.markdown('<div class="section-divider"></div>',
                        unsafe_allow_html=True)

            # ── Évolution du total mensuel ──
            st.subheader("📅 Évolution du total mensuel")

            monthly_totals = monthly_stats['monthly_totals'].copy()
            monthly_totals['mois'] = monthly_totals['mois'].astype(str)

            import plotly.graph_objects as go
            fig_total = go.Figure()

            # Ligne du total mensuel
            fig_total.add_trace(go.Scatter(
                x=monthly_totals['mois'],
                y=monthly_totals['total_mensuel'],
                mode='lines+markers',
                name='Total mensuel',
                line=dict(color='#2980B9', width=3),
                marker=dict(size=10, color='#2980B9'),
                fill='tozeroy',
                fillcolor='rgba(41, 128, 185, 0.1)',
                hovertemplate=(
                    "Mois: %{x}<br>"
                    "Total: %{y:.2f}€<extra></extra>"
                )
            ))

            # Ligne de référence budget
            fig_total.add_hline(
                y=total_budget,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Budget: {total_budget:.0f}€",
                annotation_position="top right"
            )

            # Ligne de référence moyenne
            fig_total.add_hline(
                y=avg_monthly,
                line_dash="dot",
                line_color="orange",
                annotation_text=f"Moyenne: {avg_monthly:.0f}€",
                annotation_position="bottom right"
            )

            fig_total.update_layout(
                xaxis_title="Mois",
                yaxis_title="Montant (€)",
                height=380,
                plot_bgcolor='rgba(240,240,240,0.3)',
                yaxis=dict(showgrid=True, gridcolor='white'),
                legend=dict(orientation="h", y=1.1)
            )

            st.plotly_chart(fig_total, use_container_width=True)

        else:
            st.warning(
                "⚠️ Veuillez sélectionner au moins une catégorie."
            )

    # ════════════════════════════════════════════
    # TAB 5 : GÉNÉRATION DU RAPPORT
    # ════════════════════════════════════════════
    with tab5:
        st.subheader("📄 Générer et Télécharger le Rapport")

        # ── Configuration du rapport ──
        col1, col2 = st.columns(2)

        with col1:
            report_month = st.selectbox(
                "📅 Mois du rapport",
                options=["Toute la période"] + available_months,
                index=0,
                key="report_month"
            )

        with col2:
            report_format = st.radio(
                "📁 Format du rapport",
                options=["PDF", "CSV (ZIP)"],
                horizontal=True
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Aperçu du rapport ──
        st.subheader("👁️ Aperçu du rapport")

        # Préparation des données pour le rapport
        report_month_filter = None \
            if report_month == "Toute la période" \
            else report_month

        report_category_ratios = processor.compute_category_ratios(
            df, selected_month=report_month_filter
        )

        report_actual = (
            df[df['est_dépense'] &
               (df['mois_label'] == report_month
                if report_month_filter else True)]
            .groupby('catégorie')['montant_abs']
            .sum()
            .to_dict()
        )

        report_budget_eval = budget_manager.evaluate_budget(report_actual)

        report_savings = budget_manager.compute_savings_progress(
            monthly_stats['monthly_totals']
        )

        # Onglets d'aperçu
        preview_tab1, preview_tab2, preview_tab3 = st.tabs([
            "Catégories", "Budget", "Épargne"
        ])

        with preview_tab1:
            st.dataframe(
                report_category_ratios,
                use_container_width=True,
                hide_index=True
            )

        with preview_tab2:
            st.dataframe(
                report_budget_eval,
                use_container_width=True,
                hide_index=True
            )

        with preview_tab3:
            st.dataframe(
                report_savings['savings_df'],
                use_container_width=True,
                hide_index=True
            )

        st.markdown('<div class="section-divider"></div>',
                    unsafe_allow_html=True)

        # ── Bouton de téléchargement ──
        st.subheader("⬇️ Télécharger")

        if st.button("🔄 Générer le rapport", type="primary"):
            with st.spinner("Génération du rapport en cours..."):
                try:
                    if report_format == "PDF":
                        # Génération PDF
                        pdf_bytes = report_gen.generate_pdf(
                            category_ratios=report_category_ratios,
                            budget_eval=report_budget_eval,
                            savings_data=report_savings,
                            monthly_stats=monthly_stats,
                            selected_month=report_month
                        )

                        # Nom du fichier
                        date_str = datetime.now().strftime('%Y%m%d_%H%M')
                        filename = f"rapport_financier_{date_str}.pdf"

                        st.download_button(
                            label="📥 Télécharger le PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            type="primary"
                        )
                        st.success("✅ PDF généré avec succès !")

                    else:
                        # Génération CSV ZIP
                        zip_bytes = report_gen.generate_csv(
                            category_ratios=report_category_ratios,
                            budget_eval=report_budget_eval,
                            savings_data=report_savings,
                            transactions=df[[
                                'date', 'libellé',
                                'montant', 'catégorie'
                            ]]
                        )

                        date_str = datetime.now().strftime('%Y%m%d_%H%M')
                        filename = f"rapport_financier_{date_str}.zip"

                        st.download_button(
                            label="📥 Télécharger le ZIP (CSV)",
                            data=zip_bytes,
                            file_name=filename,
                            mime="application/zip",
                            type="primary"
                        )
                        st.success(
                            "✅ Fichiers CSV générés avec succès !"
                        )

                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération : {str(e)}")


# ─────────────────────────────────────────────
# Fonctions d'aide (Helpers)
# ─────────────────────────────────────────────
def _show_welcome_screen():
    """Écran d'accueil affiché lorsqu'aucun fichier n'est importé"""

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            "### 📁 Étape 1\n"
            "Importez votre relevé bancaire\n"
            "(CSV ou Excel) depuis la barre latérale"
        )
    with col2:
        st.info(
            "### ⚙️ Étape 2\n"
            "Définissez votre budget mensuel\n"
            "par catégorie et votre objectif d'épargne"
        )
    with col3:
        st.info(
            "### 📊 Étape 3\n"
            "Analysez vos dépenses et\n"
            "téléchargez votre rapport PDF ou CSV"
        )

    st.markdown("---")
    st.markdown("### 📋 Format attendu du fichier")

    # Données d'exemple
    sample_data = pd.DataFrame({
        'date': ['01/01/2024', '02/01/2024', '05/01/2024'],
        'libellé': ['CARREFOUR MARKET', 'SNCF BILLET', 'NETFLIX'],
        'montant': [-45.30, -32.00, -13.99],
    })

    st.dataframe(sample_data, use_container_width=True, hide_index=True)
    st.caption(
        "💡 Les dépenses doivent être en montants négatifs, "
        "les revenus en positifs"
    )


# A supprimer 
def _generate_sample_csv() -> bytes:
    """
    Génère un fichier CSV d'exemple pour le test.
    Fournit des données réalistes pour que l'utilisateur puisse tester l'app immédiatement.
    """
    sample_data = """date;libellé;montant
01/01/2024;VIREMENT SALAIRE;2500.00
02/01/2024;LOYER JANVIER;-800.00
03/01/2024;CARREFOUR MARKET;-67.50
04/01/2024;SNCF BILLET PARIS;-45.00
05/01/2024;NETFLIX ABONNEMENT;-13.99
06/01/2024;AMAZON COMMANDE;-89.99
07/01/2024;RESTAURANT LE BISTRO;-32.50
08/01/2024;PHARMACIE CENTRALE;-18.40
09/01/2024;LIDL COURSES;-54.20
10/01/2024;UBER TRAJET;-12.30
11/01/2024;SPOTIFY PREMIUM;-9.99
12/01/2024;ZARA VETEMENTS;-75.00
13/01/2024;MCDO REPAS;-11.50
14/01/2024;STATION TOTAL ESSENCE;-60.00
15/01/2024;CREDIT IMMOBILIER;-350.00
01/02/2024;VIREMENT SALAIRE;2500.00
02/02/2024;LOYER FEVRIER;-800.00
03/02/2024;MONOPRIX COURSES;-92.30
04/02/2024;RATP NAVIGO;-86.40
05/02/2024;DISNEY+ ABONNEMENT;-8.99
06/02/2024;FNAC LIVRE;-24.99
07/02/2024;SUSHI RESTAURANT;-45.00
08/02/2024;MEDECIN CONSULTATION;-25.00
09/02/2024;INTERMARCHE COURSES;-78.60
10/02/2024;BLABLACAR TRAJET;-15.00
11/02/2024;CANAL+ ABONNEMENT;-20.99
12/02/2024;H&M VETEMENTS;-55.00
13/02/2024;BURGER KING REPAS;-13.80
14/02/2024;PARKING CENTRE VILLE;-8.50
15/02/2024;CREDIT IMMOBILIER;-350.00
01/03/2024;VIREMENT SALAIRE;2500.00
02/03/2024;LOYER MARS;-800.00
03/03/2024;LECLERC COURSES;-110.40
04/03/2024;SNCF ABONNEMENT;-75.00
05/03/2024;NETFLIX ABONNEMENT;-13.99
06/03/2024;DECATHLON SPORT;-120.00
07/03/2024;CINEMA UGC;-12.50
08/03/2024;DENTISTE;-80.00
09/03/2024;ALDI COURSES;-45.30
10/03/2024;UBER TRAJET;-9.80
11/03/2024;SFR MOBILE;-19.99
12/03/2024;AMAZON COMMANDE;-34.99
13/03/2024;PIZZERIA NAPOLI;-28.00
14/03/2024;AUTOROUTE PEAGE;-22.40
15/03/2024;CREDIT IMMOBILIER;-350.00"""

    return sample_data.encode('utf-8-sig')