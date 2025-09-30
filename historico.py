import matplotlib.pyplot as plt
import os
import pandas as pd
from scipy.stats import skew, kurtosis
import streamlit as st
import plotly.express as px
import seaborn as sns

from globais import *
from translations import set_language, get_translation


def app():
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

    pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = carrega_ini()

    st.title(t["historico_dos_testes"])
    st.markdown(f"### {t['dados_da_contagem']}")
    # st.write(st.session_state.resultados_contagem)

    list_respostas_diretorio = os.listdir(pasta_sala_equipamento)

    list_respostas = []
    for i in list_respostas_diretorio:
        i = i[:-4]
        list_respostas.append(i)

    list_respostas.insert(0, '')


    st.info(t["storage_directory_info"].format(dir=pasta_sala_equipamento))
    escolha_equipamento = st.selectbox(t["equipment_ids_title"], list_respostas,
                                       format_func=lambda x: t["select_option"] if x == '' else x)

    if escolha_equipamento == '':
        st.empty()
    else:
        escolha_equipamento = escolha_equipamento + '.csv'
        st.markdown(f"## {escolha_equipamento[:-4]}")
        aa = os.path.join(pasta_sala_equipamento, escolha_equipamento)
        id_sala_um = pd.read_csv(aa, sep=";")
        if lang == "pt":
            col_map = {
                "equipment_room": "Sala do equipamento",
                "image_name": "Nome da Imagem",
                "evaluation_date": "Data da avaliação",
                "result": "Parecer",
                "fibers": "Fibras",
                "specks": "Microcalcificações",
                "masses": "Massas",
                "kVp": "kVp",
                "mAs": "mAs",
                "AEC": "AEC",
                "Dose": "Dose (dGy)",
                "anode_material": "Material do ânodo",
                "filter_material": "Material do filtro",
                "fov_dimension": "Dimensão do FOV",
                "phantom_distance": "Distância até o phantom",
                "detector_distance": "Distância até o detector",
                "filter_type": "Tipo de filtro",
                "focal_spot": "Ponto focal",
                "phantom_thickness": "Espessura do phantom",
                "grid": "Grade",
                "mean": "Média",
                "variance": "Variância",
                "skewness": "Assimetria",
                "kurtosis": "Curtose",
                "SNR": "SNR",
                "CNR": "CNR",
                "X_BG": "X_BG",
                "Sigma": "Sigma",
                "X_ROI": "X_ROI"
            }
        if lang == "en":
            col_map = {
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
                "mean": "Mean",
                "variance": "Variance",
                "skewness": "Skewness",
                "kurtosis": "Kurtosis",
                "SNR": "SNR",
                "CNR": "CNR",
                "X_BG": "X_BG",
                "Sigma": "Sigma",
                "X_ROI": "X_ROI"
            }

        id_sala_um = id_sala_um.rename(columns=col_map)
        id_sala_um = id_sala_um.loc[:, ~id_sala_um.columns.duplicated()]
        if "Dose (dGy)" in id_sala_um.columns:
            idx = id_sala_um.columns.get_loc("Dose (dGy)")
            id_sala_um.insert(idx, "Dose (mGy)", pd.to_numeric(id_sala_um["Dose (dGy)"], errors="coerce") * 100)
            id_sala_um = id_sala_um.drop(columns=["Dose (dGy)"])
        if "CNR" in id_sala_um.columns and "Dose (mGy)" in id_sala_um.columns:
            id_sala_um["FOM"] = (pd.to_numeric(id_sala_um["CNR"], errors="coerce") ** 2) / id_sala_um["Dose (mGy)"]
        if "FOM" in id_sala_um.columns:
            fom_col = id_sala_um.pop("FOM")
            if "SNR" in id_sala_um.columns:
                idx = id_sala_um.columns.get_loc("SNR") + 1
            elif "CNR" in id_sala_um.columns:
                idx = id_sala_um.columns.get_loc("CNR") + 1
            else:
                idx = len(id_sala_um.columns)
            id_sala_um.insert(idx, "FOM", fom_col)
        st.write(id_sala_um)


        st.markdown(f"## {t['graficos_titulo'].format(equipamento=escolha_equipamento[:-4])}")

        st.write(f"### {t['periodo_visualizacao']}")
        print(id_sala_um.columns)

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.selectbox(
                t["selecione_data_inicio"], id_sala_um[t["data_da_avaliacao"]])

        with col2:
            data_fim = st.selectbox(
                t['selecione_data_fim'], id_sala_um[t["data_da_avaliacao"]])

            #data_fim = st.selectbox('Selecione a data de ínicio do período', [datetime.date.today()])

        with col1:
            st.write("### " + t["fibras"])
            id_sala_um[t["data_da_avaliacao"]] = pd.to_datetime(id_sala_um[t["data_da_avaliacao"]], errors='coerce')
            data_inicio = pd.to_datetime(data_inicio) - pd.Timedelta(days=365)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=365)

            linha_base_fibras = [4] * len(id_sala_um[t["fibras"]])

            fig, ax = plt.subplots()
            ax.plot_date(id_sala_um[t["data_da_avaliacao"]], id_sala_um[t["fibras"]])
            ax.plot(id_sala_um[t["data_da_avaliacao"]], linha_base_fibras, 'r--')
            ax.grid()
            fig.autofmt_xdate()
            ax.set_ylim(0, 6.5)
            ax.set_xlim([data_inicio, data_fim])
            ax.set_title(t["grafico_fibras_titulo"])
            plt.tight_layout()
            st.pyplot(fig)

        with col2:
            st.write("### " + t["microcalcificacoes"])
            linha_base_specks = []
            data_inicio = pd.to_datetime(data_inicio) - pd.Timedelta(days=365)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=365)
            for i in range(len(id_sala_um[t["microcalcificacoes"]])):
                linha_base_specks.append(3)

            fig, ax = plt.subplots()
            ax.plot_date(id_sala_um[t["data_da_avaliacao"]],
                         id_sala_um[t["microcalcificacoes"]])
            ax.plot(id_sala_um[t["data_da_avaliacao"]], linha_base_specks, 'r--')
            ax.grid()
            fig.autofmt_xdate()
            ax.set_ylim(0, 5.5)
            ax.set_xlim([data_inicio, data_fim])
            ax.set_title(t["grafico_microcalcificacoes_titulo"])
            plt.tight_layout()
            st.pyplot(fig)

        with col1:
            st.write("### " + t["massas"])
            data_inicio = pd.to_datetime(data_inicio) - pd.Timedelta(days=365)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=365)
            fig, ax = plt.subplots()
            ax.plot_date(id_sala_um[t["data_da_avaliacao"]], id_sala_um[t["massas"]])
            ax.plot(id_sala_um[t["data_da_avaliacao"]], linha_base_specks, 'r--')
            ax.grid()
            fig.autofmt_xdate()
            ax.set_ylim(0, 5.5)
            ax.set_xlim([data_inicio, data_fim])
            ax.set_title(t["grafico_massas_titulo"])
            plt.tight_layout()
            st.pyplot(fig)

        with col2:
            st.write('### CNR')
            data_inicio = pd.to_datetime(data_inicio) - pd.Timedelta(days=365)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=365)
            fig, ax = plt.subplots()
            ax.plot_date(id_sala_um[t["data_da_avaliacao"]], id_sala_um['CNR'])
            ax.grid()
            fig.autofmt_xdate()
            ax.set_xlim([data_inicio, data_fim])
            ax.set_title(t["grafico_cnr_titulo"])
            plt.tight_layout()
            st.pyplot(fig)

        with col1:
            st.write('### SNR')
            data_inicio = pd.to_datetime(data_inicio) - pd.Timedelta(days=365)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=365)
            fig, ax = plt.subplots()
            ax.plot_date(id_sala_um[t["data_da_avaliacao"]], id_sala_um['SNR'])
            ax.grid()
            fig.autofmt_xdate()
            ax.set_xlim([data_inicio, data_fim])
            ax.set_title(t["grafico_snr_titulo"])
            plt.tight_layout()
            st.pyplot(fig)


        df_plot = id_sala_um[
            ['Dose (mGy)', 'CNR', t["material_anodo"], t["material_filtro"], t["kVp"], t["mAs"], t["nome_da_imagem"]]].dropna()
        df_plot['combo'] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="Dose (mGy)",
            y="CNR",
            color="combo",
            hover_data={
                "Dose (mGy)": True,
                "CNR": True,
                t["kVp"]: True,
                t["mAs"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="CNR vs Dose (mGy)",
            labels={"Dose (mGy)": "Dose (mGy)", "CNR": "CNR", "combo": t["Anode / Filter"]}
        )
        st.plotly_chart(fig, use_container_width=True)


        df_plot = id_sala_um[
            ['Dose (mGy)', 'SNR', t["material_anodo"], t["material_filtro"], t["kVp"], t["mAs"], t["nome_da_imagem"]]].dropna()
        df_plot['combo'] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="Dose (mGy)",
            y="SNR",
            color="combo",
            hover_data={
                "Dose (mGy)": True,
                "SNR": True,
                t["kVp"]: True,
                t["mAs"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="SNR vs Dose (mGy)",
            labels={"Dose (mGy)": "Dose (mGy)", "SNR": "SNR", "combo": t["Anode / Filter"]}
        )
        st.plotly_chart(fig, use_container_width=True)


        df_plot = id_sala_um[["kVp", "CNR", t["material_anodo"], t["material_filtro"], t["mAs"], t["nome_da_imagem"]]].dropna()
        df_plot['combo'] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="kVp",
            y="CNR",
            color="combo",
            hover_data={
                "kVp": True,
                "CNR": True,
                t["mAs"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="CNR vs kVp",
            labels={"kVp": "kVp", "CNR": "CNR", "combo": t["Anode / Filter"]}
        )
        st.plotly_chart(fig, use_container_width=True)


        df_plot = id_sala_um[["kVp", "SNR", t["material_anodo"], t["material_filtro"], t["mAs"], t["nome_da_imagem"]]].dropna()
        df_plot["combo"] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="kVp",
            y="SNR",
            color="combo",
            hover_data={
                "kVp": True,
                "SNR": True,
                t["mAs"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="SNR vs kVp",
            labels={
                "kVp": "kVp",
                "SNR": "SNR",
                "combo": t["Anode / Filter"]
            }
        )
        st.plotly_chart(fig, use_container_width=True)


        df_plot = id_sala_um[["mAs", "SNR", t["material_anodo"], t["material_filtro"], t["kVp"], t["nome_da_imagem"]]].dropna()
        df_plot["combo"] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="mAs",
            y="SNR",
            color="combo",
            hover_data={
                "mAs": True,
                "SNR": True,
                t["kVp"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="SNR vs mAs",
            labels={
                "mAs": "mAs",
                "SNR": "SNR",
                "combo": t["Anode / Filter"]
            }
        )
        st.plotly_chart(fig, use_container_width=True)


        df_plot = id_sala_um[["mAs", "CNR", t["material_anodo"], t["material_filtro"], t["kVp"], t["nome_da_imagem"]]].dropna()
        df_plot["combo"] = df_plot[t["material_anodo"]].astype(str) + ' / ' + df_plot[t["material_filtro"]].astype(str)
        fig = px.scatter(
            df_plot,
            x="mAs",
            y="CNR",
            color="combo",
            hover_data={
                "mAs": True,
                "CNR": True,
                t["kVp"]: True,
                t["material_anodo"]: True,
                t["material_filtro"]: True,
                t["nome_da_imagem"]: True,
                "combo": False
            },
            title="CNR vs mAs",
            labels={
                "mAs": "mAs",
                "CNR": "CNR",
                "combo": t["Anode / Filter"]
            }
        )
        st.plotly_chart(fig, use_container_width=True)



        # st.markdown(f'### Gráfico de dispersão')
        # st.write(f'Os valores médios da matriz de pixel de cada imagem *versus* sua variância')
        # col3, col4 = st.columns([2, 1])
        # with col3:
        #    fig1 = px.scatter(id_sala_um, x='Media', y='Variancia',
        # color='Parecer', hover_data=['Nome da Imagem'])
        # st.plotly_chart(fig1)
