import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# URL de la página de búsqueda de legislación en el BOE
base_url = "https://www.boe.es/buscar/legislacion_ava.php?campo%5B0%5D=ID_SRC&dato%5B0%5D=&operador%5B0%5D=and&campo%5B1%5D=NOVIGENTE&operador%5B1%5D=and&campo%5B2%5D=CONSO&operador%5B3%5D=and&campo%5B3%5D=TITULOS&dato%5B3%5D=&operador%5B3%5D=and&campo%5B4%5D=ID_RNGS&dato%5B4%5D=1290&operador%5B4%5D=and&campo%5B5%5D=ID_DEMS&dato%5B5%5D=&operador%5B5%5D=and&campo%5B6%5D=MAT.DESCRIPCION&dato%5B6%5D=&operador%5B6%5D=and&campo%5B7%5D=DOC&dato%5B7%5D=&operador%5B7%5D=and&campo%5B8%5D=NBOS&dato%5B8%5D=&operador%5B8%5D=and&campo%5B9%5D=NOF&dato%5B9%5D=&operador%5B9%5D=and&campo%5B10%5D=DOC&dato%5B10%5D=&operador%5B11%5D=and&campo%5B11%5D=FPU&dato%5B11%5D%5B0%5D=2010-01-01&dato%5B11%5D%5B1%5D=2023-12-31&operador%5B12%5D=and&campo%5B12%5D=FAP&dato%5B12%5D%5B0%5D=&dato%5B12%5D%5B1%5D=&page_hits=2000&sort_field%5B0%5D=PESO&sort_order%5B0%5D=desc&sort_field%5B1%5D=REF&sort_order%5B1%5D=asc&accion=Buscar"
os.makedirs("data/documentos_boe_pdf", exist_ok=True)

response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Buscar los enlaces a los documentos en los elementos con la clase 'resultado-busqueda-link-defecto'
links = soup.find_all('a', class_='resultado-busqueda-link-defecto', href=True)

for link in links:
    # Obtener la URL completa del documento (link es un enlace relativo, por lo que lo hacemos absoluto)
    doc_url = urljoin(base_url, link['href'])

    print(f"Accediendo a la página del documento: {doc_url}")

    doc_page_response = requests.get(doc_url)
    doc_page_soup = BeautifulSoup(doc_page_response.text, 'html.parser')

    # Buscar el enlace al archivo PDF en la página del documento
    pdf_link = doc_page_soup.find('a', href=True, text='PDF')
    
    if pdf_link:
        # Obtener la URL del PDF
        pdf_url = urljoin(doc_url, pdf_link['href'])

        # Obtener el nombre del archivo PDF
        file_name = pdf_url.split('/')[-1]

        # Descargar el archivo PDF
        print(f"Descargando {file_name} desde {pdf_url} ...")

        file_response = requests.get(pdf_url)

        if file_response.status_code == 200:
            with open(os.path.join("documentos_boe_pdf", file_name), 'wb') as f:
                f.write(file_response.content)
        else:
            print(f"Error al descargar {file_name}: {file_response.status_code}")
    else:
        print(f"No se encontró el enlace al PDF para {doc_url}")

print("Descarga completada.")
