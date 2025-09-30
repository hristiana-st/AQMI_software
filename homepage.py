import pandas as pd
from scipy.stats import skew, kurtosis
import streamlit as st
import tkinter as tk
from tkinter import filedialog
import time


from globais import *
from translations import set_language, get_translation

#Layout
st.set_page_config(layout="wide")

def form_callback():
    pass
    
def muda_caminho_app(dirname):
    atualiza_ini("path", "pasta_raiz", dirname + "/")
    pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = carrega_ini()
    verifica_pastas()
    verifica_csv(pasta_csv)
    return pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens,  pasta_raiz

def app():
    if "language" not in st.session_state:
        st.session_state.language = "en"
    lang = st.session_state.language

    lang = st.sidebar.selectbox(
        "🌍 Idioma / Language",
        ["pt", "en"],
        index=["pt", "en"].index(st.session_state.language),
        format_func=lambda x: {"pt": "Português", "en": "English"}[x]
    )

    st.session_state.language = lang
    set_language(lang)
    t = get_translation()

    verifica_pastas()
    pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = carrega_ini()
    verifica_csv(pasta_csv)

    #st.title
    st.markdown(f"<h1 style='text-align: center; color: bold;'>{t['software_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: bold;'>{t['software_subtitle']}</h2>", unsafe_allow_html=True)

    st.write(t['developed_by'])
    st.write(t['oriented_by'])

    st.markdown(f"### {t['instructions_title']}")
    instructions = t['instructions_list']
    for i, instr in enumerate(instructions, start=1):
        st.write(f"{i}) {instr}")
    
    st.write('---')
    
    # Set up tkinter
    root = tk.Tk()
    root.withdraw()

    # Make folder picker dialog appear on top of other windows
    root.wm_attributes('-topmost', 1)

    # Folder picker button
    st.write(t["storage_dir_label"] + pasta_raiz)
    clicked = st.button(t["change_storage_dir_button"])

    if clicked:
        dirname = st.text_input(t["selected_dir_label"], filedialog.askdirectory(master=root))
        if arruma_path(dirname) != pasta_raiz:
            pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = muda_caminho_app(dirname)

    df_equipamentos = pd.read_csv(pasta_csv + '/Header.csv', sep=';')

    list_df_equipamentos = list(df_equipamentos.id)

    equipamentos = st.selectbox(t["view_registered_equipments"], list_df_equipamentos)

    cadastro_equipamento = st.checkbox(t["select_to_register_new_equip"])

    if cadastro_equipamento:
        form = st.form(key='my_form')
        list_respostas = []
        a = form.number_input(t["how_many_to_register"], min_value=0, max_value=10, step=1)
        a = int(a)
        submit_button = form.form_submit_button(label=t["advance_button"], on_click=form_callback)

        st.markdown(f"### {t['equipment_ids_title']}")

        df = pd.read_csv(pasta_csv + '/Header.csv', sep=';')

        for i in range(a):
            respota = st.text_input(f"{t['enter_equipment_id']}{i+1}: ")
            df.loc[len(df.index)] = [respota]
            list_respostas.append(respota)

        button_save = st.button(t["save_data_button"])
        if button_save:
            df.to_csv(pasta_csv+'/Header.csv', sep=';', index=False)
            with st.spinner(t["loading_message"]):
                time.sleep(1.2)
            st.success(t["success_message"])