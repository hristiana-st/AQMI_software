import matplotlib.pyplot as plt
import os
import pandas as pd
from scipy.stats import skew, kurtosis
import streamlit as st
from PIL import Image
from globais import *
from translations import set_language, get_translation

# Função para plotar a imagem
def plot_image(img, nome):
    fig, ax = plt.subplots()
    ax.imshow(img, cmap='gray')
    ax.set_title(f'{nome}', fontsize=8)
    return fig


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
    st.title(t["indicadores_adicionais"])
    st.write(t["indicadores_qualidade_imagem_nao_exigidos"])
    referencias = st.expander(t["descricao"])
    with referencias:
        st.write(t["descricao_indicadores"])
        st.write(t["lista_indicadores"])
        st.latex(t["formula_snr"])
        st.write(t["descricao_cnr"])
        st.latex(t["formula_cnr"])
        st.write(t["descricao_fom"])
        st.latex(t["formula_fom"])
        st.write(t["explicacao_formula"])
        st.write('''
                BORG, M.; BADR, I.; ROYLE, G. The use of a figure-of-merit (fom) for optimisation in digital mammography: a literature review. Radiation Protection Dosimetry, v. 151, n. 1, p.81–88, 2012. \n
                1 - Martí Villarreal, Oscar Ariel. Otimização da mamografia digital variando a glandularidade. Dissertação (Mestrado) - Ilhéus, BA: UESC, 2019.\n 
                2 - GUZMÁN, V. C.; RESTREPO, H. D. B.; HURTADO, E. S. Natural scene statistics of mammography accreditation phantom images. XXII Symposium on Image, Signal Processing and Artificial Vision, 2019. \n
                3 - XAVIER, A. C. da S. Dosimetria e qualidade da imagem em mamografia digital. Dissertação (Mestrado) — Universidade Federal de Pernambuco, 2015.

                ''')

    st.info(t["diretorio_armazenamento"].format(pasta=pasta_indicadores))
    #st.write(st.session_state.path_sala_imagens)
    list_respostas_diretorio = os.listdir(pasta_sala_equipamento)


    list_respostas = []
    for i in list_respostas_diretorio:
        i = i[:-4]
        list_respostas.append(i)

    list_respostas.insert(0,'')


    escolha_imagem = st.selectbox(
        t["selecionar_id_indicadores"],
        list_respostas,
        format_func=lambda x: t["selecione_uma_opcao"] if x == '' else x
    )

    if escolha_imagem == '':
        st.empty()
    else:
        imagens_diretorio = os.listdir(pasta_sala_imagens + f'\{escolha_imagem}')

        list_respostas = []
        for i in imagens_diretorio:
            i = i[:-4]
            list_respostas.append(i)

        list_respostas.insert(0,'')

        option = st.selectbox(t["selecione_imagem"], list_respostas,
                              format_func = lambda x: t["selecione_uma_opcao"] if x == '' else x)

        if option == '':
            st.empty()
        else:
            st.write(f'### {t["indicadores_adicionais_da_imagem"].format(img=option)}')

            st.markdown(f"### {t['imagem_titulo']}")

            aa = f'{pasta_sala_imagens}\\{escolha_imagem}\\{option}.png'
            image = Image.open(aa)

            st.image(image, caption=t["imagem_legenda"].format(img=option))

            caminho_sala_escolhida = f'{pasta_sala_equipamento}\\{escolha_imagem}.csv'
            dados = pd.read_csv(caminho_sala_escolhida, sep=';')

            for i in range(len(dados)):
                if dados.iloc[i]["image_name"] == option + '.dcm':
                    linha = dados.iloc[i]
                    break

            st.markdown(f"### {t['titulo_indicadores']}")

            path_indicadores_cnr = pasta_indicadores + f'\\CNR_{option}.dcm.png'
            file_cnr = Image.open(path_indicadores_cnr)

            coluna_hist, coluna_indicadores = st.columns([2, 1])
            with coluna_hist:
                st.image(file_cnr, caption=t["caption_cnr"].format(imagem=option))
            with coluna_indicadores:
                #st.markdown("##### Razão Sinal Ruído")
                st.markdown(f'**SNR** = {float(linha.SNR):.7f}')
                #st.markdown("##### Razão Contraste Ruído")
                st.markdown(f'**CNR** = {float(linha.CNR):.7f}')
                a = linha['Dose (dGy)']
                aa = linha.CNR ** 2
                aaa = float(a) * 100
                FOM = aa / aaa
                #st.markdown("##### Figura de Mérito")
                st.markdown(f'**FOM** = {float(FOM):.7f}')
                calc1 = f'{linha.X_BG:.5f}'
                calc2 = f'{linha.X_ROI:.5f}'
                calc3 = f'{linha.Sigma:.5f}'
                st.write(r'$\bar{X}_{BG}$ =', calc1)
                st.write(r'$\bar{X}_{ROI}$ =', calc2)
                st.write(r'$\sigma_{BG}$ =', calc3)

            # Buscando as métricas do histograma
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### {t['histograma_titulo']}")
                iuug = Image.open(pasta_indicadores + f'\{option}.dcm.png')
                st.image(iuug, caption=t["histograma_legenda"].format(imagem=option))
            with col2:
                st.markdown(f"### {t['metricas_estatisticas']}")
                st.write(f'{t["media"]}: {float(linha["mean"]):.4f}')
                st.write(f'{t["variancia"]}: {float(linha["variance"]):.4f}')
                st.write(f'{t["skewness"]}: {float(linha["skewness"]):.4f}')
                st.write(f'{t["kurtosis"]}: {float(linha["kurtosis"]):.4f}')

            espaco_vazio = st.empty()
            espaco_vazio.write('')
