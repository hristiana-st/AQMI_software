import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

from globais import *
from translations import set_language, get_translation

def app():
    # -------------------
    # Language Setup
    # -------------------
    if "language" not in st.session_state:
        st.session_state.language = "en"

    lang = st.sidebar.selectbox(
        "🌍 Idioma / Language",
        ["pt", "en"],
        index=["pt", "en"].index(st.session_state.language),
        format_func=lambda x: {"pt": "Português", "en": "English"}[x]
    )

    st.session_state.language = lang
    set_language(lang)
    t = get_translation()

    # -------------------
    # Paths
    # -------------------
    pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = carrega_ini()

    st.title(t["historico_dos_testes"])
    st.markdown(f"### {t['dados_da_contagem']}")

    # -------------------
    # Equipment Selection
    # -------------------
    list_respostas_diretorio = os.listdir(pasta_sala_equipamento)
    list_respostas = [f[:-4] for f in list_respostas_diretorio]
    list_respostas.insert(0, '')

    st.info(t["storage_directory_info"].format(dir=pasta_sala_equipamento))
    escolha_equipamento = st.selectbox(
        t["equipment_ids_title"],
        list_respostas,
        format_func=lambda x: t["select_option"] if x == '' else x
    )

    if escolha_equipamento == '':
        st.stop()

    # -------------------
    # Load CSV
    # -------------------
    escolha_equipamento_file = escolha_equipamento + '.csv'
    st.markdown(f"## {escolha_equipamento}")
    aa = os.path.join(pasta_sala_equipamento, escolha_equipamento_file)
    id_sala_um = pd.read_csv(aa, sep=";")

    # -------------------
    # Column renaming
    # -------------------
    col_map_en = {
        "equipment_room": "Equipment room",
        "image_name": "Image name",
        "evaluation_date": "Evaluation date",
        "result": "Result",
        "fibers": "Fibers",
        "specks": "Microcalcifications",
        "masses": "Masses",
        "kVp": "kVp",
        "mAs": "mAs",
        "AEC": "AEC",
        "Dose": "Dose (dGy)",
        "anode_material": "Anode material",
        "filter_material": "Filter material",
        "fov_dimension": "FOV dimension",
        "phantom_distance": "Phantom distance",
        "detector_distance": "Detector distance",
        "filter_type": "Filter type",
        "focal_spot": "Focal spot",
        "phantom_thickness": "Phantom thickness",
        "grid": "Grid",
        "SNR": "SNR",
        "CNR": "CNR"
    }

    id_sala_um = id_sala_um.rename(columns=col_map_en)
    id_sala_um = id_sala_um.loc[:, ~id_sala_um.columns.duplicated()]

    # -------------------
    # Dose conversion to mGy
    # -------------------
    if "Dose (dGy)" in id_sala_um.columns:
        idx = id_sala_um.columns.get_loc("Dose (dGy)")
        id_sala_um.insert(idx, "Dose (mGy)", pd.to_numeric(id_sala_um["Dose (dGy)"], errors="coerce") * 100)
        id_sala_um = id_sala_um.drop(columns=["Dose (dGy)"])

    # -------------------
    # FOM calculation
    # -------------------
    if "CNR" in id_sala_um.columns and "Dose (mGy)" in id_sala_um.columns:
        id_sala_um["FOM"] = (pd.to_numeric(id_sala_um["CNR"], errors="coerce") ** 2) / id_sala_um["Dose (mGy)"]

    # -------------------
    # Remove duplicated mean/variance columns
    # -------------------
    cols_to_keep = []
    seen = set()
    for col in id_sala_um.columns:
        key = col.lower()
        if key in ["mean", "variance"]:
            if key not in seen:
                cols_to_keep.append(col)
                seen.add(key)
        else:
            cols_to_keep.append(col)

    id_sala_um = id_sala_um[cols_to_keep]

    # -------------------
    # Full Dataset
    # -------------------
    st.markdown(f"### {t['full_dataset']}")
    st.dataframe(id_sala_um)

    # -------------------
    # Dynamic Filters
    # -------------------
    st.markdown(t["filter_instructions"])

    df_filtered = id_sala_um.copy()

    filter_cols = [
        "kVp", "mAs", "Anode material", "Filter material", "AEC",
        "Phantom thickness", "Grid", "Phantom distance",
        "Detector distance", "FOV dimension", "Filter type",
        "Focal spot", "Dose (mGy)"
    ]

    colA, colB, colC = st.columns(3)

    for i, col in enumerate(filter_cols):
        if col in df_filtered.columns:
            with [colA, colB, colC][i % 3]:
                vals = sorted(df_filtered[col].dropna().unique())
                selected = st.multiselect(col, vals, default=vals)
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

    # -------------------
    # Date filter
    # -------------------
    if "Evaluation date" in df_filtered.columns:
        df_filtered["Evaluation date"] = pd.to_datetime(df_filtered["Evaluation date"], errors="coerce")
        df_filtered = df_filtered.dropna(subset=["Evaluation date"])

        col1, col2 = st.columns(2)
        dates = df_filtered["Evaluation date"].sort_values().unique()

        with col1:
            data_inicio = st.selectbox(t["start_date"], dates)
        with col2:
            data_fim = st.selectbox(t["end_date"], dates)

        df_filtered = df_filtered[
            (df_filtered["Evaluation date"] >= data_inicio) &
            (df_filtered["Evaluation date"] <= data_fim)
        ]

    # -------------------
    # Time Series
    # -------------------
    def plot_time_series(column, limit=None, baseline=None):
        fig, ax = plt.subplots()
        ax.scatter(df_filtered["Evaluation date"], df_filtered[column])
        if baseline is not None:
            ax.axhline(baseline, linestyle="--", color="red")
        if limit:
            ax.set_ylim(limit)
        ax.grid()
        fig.autofmt_xdate()
        st.pyplot(fig)

    col1, col2 = st.columns(2)

    if "Fibers" in df_filtered.columns:
        with col1:
            st.write(t["fibers"])
            plot_time_series("Fibers", (0, 6.5), 4)

    if "Microcalcifications" in df_filtered.columns:
        with col2:
            st.write(t["specks"])
            plot_time_series("Microcalcifications", (0, 5.5), 3)

    if "Masses" in df_filtered.columns:
        with col1:
            st.write(t["masses"])
            plot_time_series("Masses", (0, 5.5), 3)

    if "CNR" in df_filtered.columns:
        with col2:
            st.write(t.get("cnr", "CNR"))
            plot_time_series("CNR")

    if "SNR" in df_filtered.columns:
        with col1:
            st.write(t.get("snr", "SNR"))
            plot_time_series("SNR")

    # -------------------
    # Scatter plots (Hover + Color + Symbol)
    # -------------------
    if "Anode material" in df_filtered.columns and "Filter material" in df_filtered.columns:
        df_filtered["Anode / Filter"] = (
                df_filtered["Anode material"] + " / " + df_filtered["Filter material"]
        )

    # Полета, които да се показват при hover
    hover_cols = [
        "Image name", "Evaluation date", "Fibers", "Microcalcifications", "Masses",
        "kVp", "mAs", "Dose (mGy)", "Anode material", "Filter material",
        "Phantom distance", "Detector distance", "Filter type",
        "Focal spot", "Phantom thickness", "Grid", "SNR", "CNR"
    ]

    metrics = ["CNR", "SNR"]
    x_vars = ["Dose (mGy)", "kVp", "mAs"]

    for metric in metrics:
        if metric not in df_filtered.columns:
            continue

        for x in x_vars:
            if x not in df_filtered.columns:
                continue

            fig = px.scatter(
                df_filtered,
                x=x,
                y=metric,
                color="Anode / Filter",
                symbol="kVp",
                hover_data={col: True for col in hover_cols if col in df_filtered.columns},
                title=f"{metric} vs {x}",
                labels={
                    x: x,
                    metric: metric,
                    "Anode / Filter": "Anode / Filter",
                    "kVp": "kVp"
                }
            )

            fig.update_traces(marker=dict(size=12))
            st.plotly_chart(fig, use_container_width=True)

