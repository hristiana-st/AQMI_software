import homepage
import avaliar_teste
import historico
import indicadores
import streamlit as st
from globais import *
from configparser import ConfigParser
import sys
import os
from pathlib import Path

if getattr(sys, "frozen", False):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    base_path = Path(__file__).parent.resolve()

os.chdir(base_path)

config = ConfigParser()
config.read("parametros.ini")


PAGES = {"Home Page / Página inicial": homepage,
         "Image Quality Test / Teste de qualidade da imagem": avaliar_teste,
         "Additional Indicators / Indicadores adicionais": indicadores,
         "Test History / Histórico dos testes": historico,
         }

criar_pasta_raiz()
verifica_pastas()
pasta_csv, pasta_indicadores, pasta_sala_equipamento, pasta_sala_imagens, pasta_raiz = carrega_ini()

#Centralizando as imagens
col1, col2, col3 = st.sidebar.columns([1,2,1])

with col1:
    st.write("")

with col2:
    logo_image = "https://github.com/ArthurMangussi/AQMI/blob/main/AQMI.png?raw=true"
    st.image(logo_image, width = 100)

with col3:
    st.write("")

st.sidebar.header("Navigation / Navegação")

selection = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
    label_visibility="collapsed"
)


c1, c2, c3 = st.sidebar.columns([1,2,1])
with c1:
    st.write("")
with c2:
    logo_ufcspa = "https://github.com/ArthurMangussi/AQIM/blob/main/ufcspa.png?raw=true"
    st.image(logo_ufcspa, width = 150)
with c3:
    st.write("")

page = PAGES[selection]
page.app()
