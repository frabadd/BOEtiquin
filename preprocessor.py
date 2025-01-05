import os
import re

import PyPDF2


def pdf_a_txt(pdf_path, txt_path):

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
    # Extrae texto de todas las páginas, empezando desde la tercera
    text = ''
    articulo_actual = None

    for page_num in range(2, len(reader.pages)):
        page = reader.pages[page_num]
        page_text = page.extract_text()

        # Elimina cualquier ocurrencia repetitiva
        page_text = re.sub(r'Página \d+', '', page_text)
        page_text = re.sub(r'Pág. \d+', '', page_text)
        page_text = re.sub(r'BOLETÍN OFICIAL DEL ESTADO', '', page_text)
        page_text = re.sub(r'LEGISLACIÓN CONSOLIDADA', '', page_text)

        page_text = page_text.replace('.\n', '.\n\n') # Insertar salto de línea después de cada frase
        page_text = page_text.replace(' \n', ' ')     # Eliminar saltos de línea que no terminan frase
        page_text = page_text.replace('\n ', ' ')

        # Dividir el texto de la página en párrafos
        lines = page_text.split('.\n\n')

        # Anteponer "Articulo X" a cada subapartado de un artículo
        for i, line in enumerate(lines):

            # Detecta cuando un artículo comienza
            match = re.search(r'Artículo \d+', line)
            if match:
                # Cuando encontramos un nuevo artículo, actualizamos el número de artículo actual
                articulo_actual = match[0].split(" ")[1]

            elif articulo_actual and line != '\n':
                # Si ya hay un artículo asignado, anteponemos "Artículo X" a la línea
                lines[i] = f'Artículo {articulo_actual} {line}'

        # Volver a juntar las líneas con saltos de línea
        page_text = '.\n\n'.join(lines)

        # Añadir el texto procesado de la página al texto final
        text += page_text

    if text:
        # Guarda el texto extraído en un archivo .txt
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)


pdf_folder = "data/documentos_boe_pdf/"
txt_folder = "data/documentos_boe_txt/"
for archivo in os.listdir(pdf_folder):
    if archivo.endswith(".pdf"):
        pdf_a_txt(pdf_folder + archivo, txt_folder + archivo.replace(".pdf", ".txt"))
