import numpy as np
import pydicom as dicom
import matplotlib.pyplot as plt
import os
import pandas as pd
import cv2
from scipy.stats import skew, kurtosis
import streamlit as st
import datetime
from scipy.stats import skew, kurtosis
from globais import *
from translations import set_language, get_translation
from skimage.util import view_as_windows

def create_circular_mask(h, w, center=None, radius=None):
    if center is None:  # use the middle of the image
        center = (int(w/2), int(h/2))
    if radius is None:  # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w-center[0], h-center[1])

    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y - center[1])**2)

    mask = dist_from_center <= radius
    return mask


def create_df_tags_dicom(imagem, imagem_dicom):
    lista_tags = []
    for tag_dicom in imagem:
        lista_tags.append(tag_dicom)

    valores = []
    atributos = []
    for i in range(0, len(lista_tags)):
        valores.append(str(lista_tags[i])[53:])
        # atributos.append(str(lista_tags[i])[:53])
        tag_int = lista_tags[i].tag
        atributos.append(f"({tag_int.group:04X},{tag_int.element:04X})")


    data = pd.DataFrame(index=[(imagem_dicom.name)[:12]],
                        columns=atributos)

    data.iloc[0] = valores

    return data

# Função para plotar a imagem


def plot_image(img, nome, color_map):
    fig, ax = plt.subplots()
    w = ax.get_xaxis()
    z = ax.get_yaxis()
    w.set_visible(False)
    z.set_visible(False)
    ax.imshow(img, cmap=color_map)
    ax.set_title(f'{nome}', fontsize=8)
    return fig

def plot_image_draw(img, nome):
    fig, axes = plt.subplots()
    center_roi_mass = (500, 90)
    center_roi_bg = (400, 180)
    raio = 40
    # Desenhando as ROIs para cálculo da CNR
    draw_circle = plt.Circle(center_roi_mass, raio,fill=False,color='white')
    draw_circle2 = plt.Circle(center_roi_bg, raio,fill=False,color='white')
    axes.set_aspect(1)
    axes.add_artist(draw_circle)
    axes.add_artist(draw_circle2)
    plt.annotate('ROI', (570, 70), color='white')
    plt.annotate('BG', (450, 200), color='white')

    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    axes.imshow(img, cmap='gray')
    axes.set_title(f'{nome}', fontsize=8)
    return fig


def plot_image_with_rois(img, center_roi_mass, center_roi_bg, radius, nome=""):
    fig, ax = plt.subplots()
    ax.imshow(img, cmap='gray')
    roi_circle = plt.Circle(center_roi_mass, radius, color='white', fill=False)
    bg_circle = plt.Circle(center_roi_bg, radius, color='white', fill=False)

    ax.add_patch(roi_circle)
    ax.add_patch(bg_circle)
    ax.axis('off')

    ax.annotate('ROI', (center_roi_mass[0] + 70, center_roi_mass[1] - 20), color='white', fontsize=8)
    ax.annotate('BG', (center_roi_bg[0] + 50, center_roi_bg[1] + 20), color='white', fontsize=8)

    if nome:
        ax.set_title(f'{nome}', fontsize=8, color='black')

    return fig

# Função para cortar a ROI fixa das imagens Valentina
def crop_ROI(imagem):
    roi = imagem.pixel_array[740:1570, 920:1700]
    return roi


def roi_CNR(img):
    corte_subROI = img[0:250, 350:650]
    roi = np.uint8(corte_subROI)
    img_negativa = cv2.bitwise_not(roi)
    return corte_subROI


# Função para calcular histograma
def histogram(imagem_cortada, t):
    bins = 2 ** 16
    hist, edges = np.histogram(imagem_cortada, bins = bins)
    fig, ax = plt.subplots()
    ax.plot(hist, label=t["histogram_label"])
    ax.set_xlabel(t["x_axis_label"])
    ax.set_ylabel(t["y_axis_label"])
    return hist, fig

def get_value_or_default(df, tag, default="N/A"):
    if tag in df.columns:
        return df[tag]
    else:
        return pd.Series([default], index=df.index)


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
    cria_arquivos_resultados_analises(pasta_csv, pasta_sala_equipamento, t)

    st.title(t["title"])
    st.write(t["intro"])

    df = pd.read_csv(pasta_csv + "/Header.csv", sep=";")
    list_respostas = list(df.id)
    list_respostas.insert(0, '')

    upload_image = st.file_uploader(t["upload"],
                                    key='1',
                                    help=t["upload_help"])
    if upload_image is None:
        st.warning(t["no_image"])
    else:
        st.info(t["storage_directory_info"].format(dir=pasta_sala_equipamento))
        nome_equipamento = st.selectbox(t["select_id"], list_respostas, format_func=lambda x: t["select_option"] if (isinstance(x, str) and x == '') else str(x))

        if nome_equipamento == '':
            st.write('')
        else:

            img_upload = dicom.dcmread(upload_image)

            # Criando o dataset para as tags DICOM
            valentina = create_df_tags_dicom(img_upload, upload_image)

            KVP = get_value_or_default(valentina, '(0018,0060)')
            MAS = get_value_or_default(valentina, '(0018,1152)')
            anodo = get_value_or_default(valentina, '(0018,1191)')
            filtro = get_value_or_default(valentina, '(0018,7050)')
            shape_fov = get_value_or_default(valentina, '(0018,1147)')
            dimension_fov = get_value_or_default(valentina, '(0018,1149)')
            organ_dose = get_value_or_default(valentina, '(0040,0316)')
            distancia_paciente = get_value_or_default(valentina, '(0018,1111)')
            distancia_detecttor = get_value_or_default(valentina, '(0018,1110)')
            filter_type = get_value_or_default(valentina, '(0018,1160)')
            focal_spot = get_value_or_default(valentina, '(0018,1190)')
            body_part_thickness = get_value_or_default(valentina, '(0018,11A0)')
            grid = get_value_or_default(valentina, '(0018,1166)')
            AEC = get_value_or_default(valentina, '(0018,7060)')
            data_aquisicao = get_value_or_default(valentina, '(0008,0022)')



            kVp = [float(x.replace("'", "").strip()) for x in KVP]
            mAs = [float(x.replace("'", "").strip()) for x in MAS]

            # Arrumando a data
            data_str = data_aquisicao.values[0].replace("'", "").strip()
            ano = int(data_str[0:4])  
            mes = int(data_str[4:6])
            dia = int(data_str[6:8])
            date_aquisition = datetime(ano, mes, dia).date()
            # Arrumando AEC
            modo_aec = AEC.tolist()[0]

            roi_cortada = crop_ROI(img_upload)
            imagem_negativada_cnr = roi_CNR(roi_cortada)
            imagem_negativada = cv2.bitwise_not(roi_cortada)
            h, w = imagem_negativada_cnr.shape[:2]

            x_offset = 350
            y_offset = 0

            st.subheader(t["adjust_roi"])
            with st.expander(t["adjust_roi"], expanded=True):
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

                with col1:
                    center_x = st.number_input("X_ROI", min_value=0, max_value=w + x_offset, value=500)
                with col2:
                    center_y = st.number_input("Y_ROI", min_value=0, max_value=h + y_offset, value=90)
                with col3:
                    center_bg_x = st.number_input("X_BG", min_value=0, max_value=w + x_offset, value=400)
                with col4:
                    center_bg_y = st.number_input("Y_BG", min_value=0, max_value=h + y_offset, value=180)
                with col5:
                    radius_roi = st.slider(t["radius"], min_value=5, max_value=100, value=40)

                fig_roi = plot_image_with_rois(imagem_negativada,
                                               center_roi_mass=(center_x, center_y),
                                               center_roi_bg=(center_bg_x, center_bg_y),
                                               radius=radius_roi)
                st.pyplot(fig_roi)


            # Calculations – local coordinates on imagem_negativada_cnr
            mask_massa = create_circular_mask(h, w, center=(center_x-x_offset, center_y-y_offset), radius=radius_roi)
            mask_bg = create_circular_mask(h, w, center=(center_bg_x-x_offset, center_bg_y-y_offset), radius=radius_roi)

            roi_massa_cortada = imagem_negativada_cnr[mask_massa]
            roi_bg_cortada = imagem_negativada_cnr[mask_bg]

            X_ROI = np.mean(roi_massa_cortada)
            X_BG = np.mean(roi_bg_cortada)
            Sigma = np.std(roi_bg_cortada)
            SNR = X_ROI / Sigma if Sigma != 0 else 0
            CNR = np.abs(X_BG - X_ROI) / Sigma if Sigma != 0 else 0

            # Calculando as métricas estatísticas para as ROIs
            path_salvar_dados_indicadores = pasta_indicadores
            dados_hist, img_hist = histogram(roi_cortada, t)
            plt.savefig(path_salvar_dados_indicadores + f'\{upload_image.name}' + '.png')  # Salvando o histograma
            media = np.mean(img_upload.pixel_array)
            variancia = np.var(img_upload.pixel_array)
            pixel_values = img_upload.pixel_array.flatten()
            assimetria = skew(pixel_values)
            curtose = kurtosis(pixel_values)

            def clean_str(value):
                if isinstance(value, list):
                    return ', '.join(str(v).replace("'", "").replace("[", "").replace("]", "").strip() for v in value)
                elif isinstance(value, str):
                    return value.replace("'", "").strip()
                else:
                    return value

            data_tags = pd.DataFrame({
                "nome_da_imagem": [upload_image.name],
                "acquisition_date": [clean_str(data_aquisicao.values[0])],
                "kVp": kVp,
                "mAs": mAs,
                "AEC": [clean_str(modo_aec)],
                "material_anodo": [clean_str(anodo.tolist())],
                "material_filtro": [clean_str(filtro.tolist())],
                "dimensao_fov": [clean_str(dimension_fov.tolist())],
                "shape_fov": [clean_str(shape_fov.tolist())],
                "Dose (dGy)": clean_str(organ_dose.tolist()),
                "distancia_phantom": [clean_str(distancia_paciente.tolist())],
                "distancia_detector": [clean_str(distancia_detecttor.tolist())],
                "tipo_filtro": [clean_str(filter_type.tolist())],
                "ponto_focal": [clean_str(focal_spot.tolist())],
                "espessura_phantom": [clean_str(body_part_thickness.tolist())],
                "grade": [clean_str(grid.tolist())]
            })

            column_translations = {
                "pt": {
                    "nome_da_imagem": "nome_da_imagem",
                    "acquisition_date": "data",
                    "kVp": "kVp",
                    "mAs": "mAs",
                    "AEC": "AEC",
                    "material_anodo": "material_anodo",
                    "material_filtro": "material_filtro",
                    "dimensao_fov": "dimensao_fov",
                    "shape_fov": "shape_fov",
                    "Dose (dGy)": "Dose (dGy)",
                    "distancia_phantom": "distancia_phantom",
                    "distancia_detector": "distancia_detector",
                    "tipo_filtro": "tipo_filtro",
                    "ponto_focal": "ponto_focal",
                    "espessura_phantom": "espessura_phantom",
                    "grade": "grade"
                },
                "en": {
                    "nome_da_imagem": "Image Name",
                    "acquisition_date": "Date",
                    "kVp": "kVp",
                    "mAs": "mAs",
                    "AEC": "AEC",
                    "material_anodo": "Anode Material",
                    "material_filtro": "Filter Material",
                    "dimensao_fov": "FOV Dimension",
                    "shape_fov": "FOV Shape",
                    "Dose (dGy)": "Dose (dGy)",
                    "distancia_phantom": "Phantom Distance",
                    "distancia_detector": "Detector Distance",
                    "tipo_filtro": "Filter Type",
                    "ponto_focal": "Focal Spot",
                    "espessura_phantom": "Phantom Thickness",
                    "grade": "Grid"
                }
            }

            # data_tags['organ_dose'] = data_tags['organ_dose'].apply(lambda x: np.fromstring(x.replace('"',''), sep=' '))
            # data_tags['distancia_paciente'] = data_tags['distancia_paciente'].apply(lambda x: np.fromstring(x.replace('"',''), sep=' '))
            # data_tags['distancia_detector'] = data_tags['distancia_detector'].apply(lambda x: np.fromstring(x.replace('"',''), sep=' '))
            # data_tags['focal_spot'] = data_tags['focal_spot'].apply(lambda x: np.fromstring(x.replace('"',''), sep=' '))
            # data_tags['body_part_thickness'] = data_tags['body_part_thickness'].apply(lambda x: np.fromstring(x.replace('"',''), sep=' '))

            with st.container():
                # Criando colunas no Dashboard
                c1, c2 = st.columns(2)

                with c1:
                    ############################# Código para input da avaliação ##################################
                    form = st.form(key='my_form', clear_on_submit=True)
                    form.write(f'{t["acquisition_date"]}: {dia}/{mes}/{ano}')
                    form.write(f'{t["automatic_exposure_control"]}: {modo_aec}')
                    n_fibras = form.number_input(
                        label=t["fibers"], min_value=0, max_value=6, step=1)
                    n_specks = form.number_input(
                        label=t["specks"], min_value=0, max_value=5, step=1)
                    n_massas = form.number_input(
                        label=t["masses"], min_value=0, max_value=5, step=1)
                    submit_button = form.form_submit_button(label=t["submit"])

                ########################## Código para dataset Valentina ##################################
                with c2:
                    # Negativando a imagem
                    imagem_negativada = cv2.bitwise_not(roi_cortada)

                    st.write(plot_image(imagem_negativada,
                                        upload_image.name, 'gray'))

            expander = st.expander(
                t["parameters_title"])
            with expander:
                st.write(f"{t['parameters_info']} {upload_image.name}.")
                translated_columns = column_translations[lang]
                data_tags_display = data_tags.rename(columns=translated_columns)
                a = data_tags_display.iloc[[0]]
                st.write(a)
            # ---------------------------------------------------------------------------------------------------------

            if submit_button:

                # Avaliando a imagem
                if n_fibras >= 4 and n_specks >= 3 and n_massas >= 3:
                    st.success(t["success"])
                    v_resultado_avaliacao = t["conforme"]
                else:
                    st.error(t["error"])
                    v_resultado_avaliacao = t["nao_conforme"]

                df = pd.DataFrame({
                    "equipment_room": nome_equipamento,
                    "image_name": upload_image.name,
                    "evaluation_date": date_aquisition,
                    "result": v_resultado_avaliacao,
                    "fibers": n_fibras,
                    "specks": n_specks,
                    "masses": n_massas,
                    "kVp": data_tags.kVp.values,
                    "mAs": data_tags.mAs.values,
                    "AEC": data_tags.AEC.values,
                    "Dose (dGy)": data_tags.get("Dose (dGy)", pd.Series()).values,
                    "anode_material": data_tags["material_anodo"].values,
                    "filter_material": data_tags["material_filtro"].values,
                    "fov_dimension": data_tags["dimensao_fov"].values,
                    "phantom_distance": data_tags["distancia_phantom"].values,
                    "detector_distance": data_tags["distancia_detector"].values,
                    "filter_type": data_tags["tipo_filtro"].values,
                    "focal_spot": data_tags["ponto_focal"].values,
                    "phantom_thickness": data_tags["espessura_phantom"].values,
                    "grid": data_tags["grade"].values,
                    "mean": [media],
                    "variance": [variancia],
                    "skewness": [assimetria],
                    "kurtosis": [curtose],
                    "SNR": SNR,
                    "CNR": CNR,
                    "X_BG": np.mean(roi_bg_cortada),
                    "Sigma": np.std(roi_bg_cortada),
                    "X_ROI": np.mean(roi_massa_cortada)
                })

                df1 = pd.read_csv(pasta_sala_equipamento +
                                  "\\" + str(nome_equipamento) + ".csv", sep=";")
                df2 = pd.concat([df, df1])
                df2.to_csv(pasta_sala_equipamento + "\\" + str(nome_equipamento) +
                           ".csv", sep=";", encoding='utf-8', index=False)

            path_sala = pasta_sala_equipamento

            roi_desenhada = plot_image_with_rois(imagem_negativada,
                                                 center_roi_mass=(center_x, center_y),
                                                 center_roi_bg=(center_bg_x, center_bg_y),
                                                 radius=radius_roi)
            roi_desenhada.savefig(path_salvar_dados_indicadores + f'\\CNR_{upload_image.name}.png')

            for item in list_respostas[1:]:
                id_sala = item
                name_pasta = f'{pasta_sala_imagens}\{id_sala}'
                try:
                    os.makedirs(name_pasta, exist_ok=True)
                except OSError as error:
                    st.write(t["dir_not_created"])

            st.write(f'### {t["Variance Map"]}')
            roi_for_variance = roi_cortada.astype(np.float32)
            win_size = 3
            pad = win_size // 2
            padded = np.pad(roi_for_variance, pad_width=pad, mode='reflect')

            from skimage.util import view_as_windows
            windows = view_as_windows(padded, (win_size, win_size))

            variance_map = np.var(windows, axis=(-1, -2))

            var_map_norm = cv2.normalize(variance_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            st.image(var_map_norm, caption=t["Variance Map"], use_container_width=True)
            variance_map_path = os.path.join(path_salvar_dados_indicadores,
                                             f'variance_map_{upload_image.name}.png')
            plt.imsave(variance_map_path, var_map_norm, cmap='gray')

            # Salvando a imagem em PNG
            bb = plot_image(imagem_negativada, upload_image.name, 'gray')
            plt.savefig(f'{pasta_sala_imagens}\{nome_equipamento}\{upload_image.name[:-4]}.png')