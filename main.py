import json
import os
import re

import faiss
import nltk
import requests
from sentence_transformers import SentenceTransformer
from transformers import pipeline

nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize

import spacy
from spacy.language import Language
from spacy_langdetect import LanguageDetector

from deep_translator import GoogleTranslator

from bertopic import BERTopic

@Language.factory("language_detector")
def create_language_detector(nlp, name):
    return LanguageDetector(language_detection_function=None)

TOKEN_LIMIT = 4096
MAX_TOKENS_RESPONSE = 100

# Detectar el idioma de la pregunta
mult_nlp = spacy.load('xx_sent_ud_sm')
mult_nlp.add_pipe('language_detector', last=True)
detected_language = "es"
similar_topics = []

role_message = """Eres un experto en derecho español, y tu tarea consiste en responder preguntas relacionadas con el Boletín Oficial del Estado (BOE) de España. Además, formas parte de un sistema RAG (Retrieval-Augmented Generation), por lo que debes responder únicamente cuando se te proporcione información suficiente sobre un tema.
1. Las respuestas deben derivarse exclusivamente del contexto proporcionado.
2. Si el contexto esta vacío, no debes proporcionar una respuesta bajo ninguna circunstancia.
3. Las respuestas deben incluir los documentos específicos que respalden la respuesta.
4. Las preguntas deben ser claras, precisas y no ambiguas.
5. Referencias prohibidas: Si no tienes información en el contexto, no indiques información externa con "sin embargo" o frases similares; simplemente indica que no puedes responder la pregunta.
6. Suficiencia de información: Si el contenido carece de información suficiente para formar una respuesta, no intentes forzar una respuesta.
NO incluyas texto adicional en la salida, solo la respuesta a la pregunta.
Asegúrate SIEMPRE de que las preguntas y respuestas sean precisas, completas y relevantes, evitando estrictamente cualquier invención o especulación o información adicional no relevante.
SIEMPRE debes incluir la referencia del documento de donde estás obteniendo la información escribiendo "Según el Artículo X del BOE-A-YYYY-ZZZZZ (Boletín Oficial del Estado)", estos documentos solo pueden ser los que se te proporcionan en el contexto.

Ejemplo de una salida bien generada:

    Contexto: From BOE-A-2018-15138.txt: están establecidos por el ordenamiento jurídico español en virtud del Derecho Internacional vigente.Artículo 4 cve: BOE-A-2018-15138. Verificable en http://www.boe.es. Núm. 268  Martes 6 de noviembre de 2018  Sec. I.   Pág. 107648. Artículo 5.  Capitalidad y sede de la Presidencia.Artículo 5 1. La capitalidad de Canarias se fija compartidamente en las ciudades de Las Palmas de Gr.
    From BOE-A-1978-31229.txt: Estas se utilizarán junto a la bandera de España en sus edificios públicos y en sus actos oficiales.Artículo 5.  La capital del Estado es la villa de Madrid.Artículo 6.  Los partidos políticos expresan el pluralismo político, concurren a la formación y mani.
    From BOE-A-2018-15138.txt: tes 6 de noviembre de 2018  Sec. I.   Pág. 107648
    Artículo 5.  Capitalidad y sede de la Presidencia.Artículo 5 1. La capitalidad de Canarias se fija compartidamente en las ciudades de Las Palmas de Gran Canaria y Santa Cruz de Tenerife, regulándose el estatuto de capitalidad por ley del Parlamento de Canarias.Artículo 5 La sede de la Presidencia de Canarias alternará entre ambas ciudades capitalinas por peri.
    From BOE-A-2018-15138.txt: Artículo 66.  Capitales insulares.Artículo 66 La capital de cada isla se fija donde se encuentra la sede de los cabildos insulares: la de El Hierro en Valverde, la de Fuerteventura en Puerto del Rosario, la de Gran Canaria en Las Palmas de Gran Canaria, la de La Gomera en San Sebastián de La Gomera, la de Lanzarote en Arrecife, la de La Palma en Santa Cruz de La Palma y la de Tenerife en Santa Cruz de Tenerife.Artículo 67.  Organización..
    From BOE-A-2018-15138.txt: as en este Estatuto de Autonomía y en las leyes, así como las que les sean transferidas o delegadas.Artículo 66.  Capitales insulares.Artículo 66 La capital de cada isla se fija donde se encuentra la sede de los cabildos insulares: la.
    From BOE-A-1978-31229.txt: Artículo 5.  La capital del Estado es la villa de Madrid.Artículo 6.  Los partidos políticos expresan el pluralismo político, concurren a la formación y manifestación de la voluntad popular y son instrumento fundamental para la participación política. Su creación y el ejercicio de su actividad son libres dentro del respeto a la Constitución y a la ley. Su estructura interna y funcionamiento deberán ser democráticos.Artículo 7.  Los sindicatos de trabajadores y las asociaciones empresariales contribuyen a la defens.
    Pregunta: ¿Cuál es la capital de España?
    Respuesta: Según el Artículo 5 del BOE-A-1978-31229 (Boletín Oficial del Estado), la capital del Estado es la villa de Madrid.

Ejemplo de una salida mal generada:
    
    Contexto: From BOE-A-2011-1638.txt: Para el desarrollo regional y el mejor ejercicio de sus competencias, la Comunidad Autónoma de Extremadura podrá constituir empresas públicas, organismos autónomos y otros entes públicos de derecho público o privado, en las formas y con los controles previstos por una ley de la 	Asamblea que garantice en todo caso la transparencia y la adecuada fiscalización de estas entidades.
    Pregunta: ¿Qué tipo de Entidades locales pueden crear las Comunidades Autónomas?"
    Respuesta: No tengo suficiente información para proporcionar una respuesta precisa. Sin embargo, puedo 	decir que según el texto proporcionado, las Comunidades Autónomas pueden constituir entidades locales como:

	* Empresas públicas
	* Organismos autónomos
	* Otros entes públicos de derecho público o privado

	Además, se menciona que las Comunidades Autónomas tienen potestad reglamentaria, prerrogativas de derecho público y autonomía para establecer su propia estructura organizativa."

Esta respuesta es incorrecta porque no incluye documentos específicos que respalden la respuesta. No debes incluir información parcial ni suponer conclusiones basadas en información incompleta.
"""

messages_chat = [
    {
        "role":"system", 
        "content": role_message
    }
]

# Función para hacer consultas al modelo
def chat_response(model, prompt, prev_response, url="http://kumo01:11434/api/chat"):

    messages_chat.append(prev_response)
    messages_chat.append({"role":"user", "content": prompt})

    total_tokens = 0
    for message in messages_chat:
        total_tokens += len(word_tokenize(message["content"])) + 3

    while total_tokens > TOKEN_LIMIT and messages_chat:
        removed_message = messages_chat.pop(1)
        total_tokens -= len(word_tokenize(removed_message["content"])) + 3

    data = {
        "model": model,
        "messages": messages_chat,
        "stream": False,
        "options":{"temperature": 0}
        
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code}, {response.text}"

    except Exception as e:
        return f"An error occurred: {str(e)}"


def extract_relevant_terms(query):
    """
    Limpia una pregunta para quedarse con términos relevantes.

    Args:
        query (str): La pregunta del usuario.

    Returns:
        list: Lista de términos relevantes.
    """

    # Cargar el modelo de spaCy
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(query.lower())

    # Lista para almacenar términos relevantes
    relevant_terms = []

    for token in doc:
        # Excluir puntuación
        if not token.is_punct and len(token.text):
            # Incluir palabras clave o aquellas con POS relevante
            if token.pos_ in {"NOUN", "VERB", "ADJ", "PROPN", "NUM"}:
                relevant_terms.append(token.lemma_)  # Agregar la forma lematizada

    return relevant_terms


def query_similar_paragraphs(complex_query, index, metadata, paragraphs, k=5, model_name="dariolopez/bge-m3-es-legal-tmp-6"):
    """
     Busca los párrafos más similares en @p index para una consulta @p complex_query.

     Args:
         complex_query (str): La consulta compleja formulada por el usuario.
         index (faiss.Index): El índice en el que se busca los párrafos similares.
         metadata (list): Lista de metadatos asociados con los párrafos del índice.
         paragraphs (list): Lista de párrafos que se comparan con la consulta.
         k (int, opcional): El número de resultados más cercanos a devolver. Por defecto es 5.
         model_name (str, opcional): El nombre del modelo de lenguaje a usar para generar los embeddings de la consulta.
                                     Por defecto es "dariolopez/bge-m3-es-legal-tmp-6".

     Returns:
         list: Una lista de tuplas, cada una conteniendo el nombre del documento, el párrafo y la distancia de similitud.
     """

    model = SentenceTransformer(model_name, device = 'cpu')
    queries = extract_relevant_terms(complex_query)
    complex_query = " ".join(queries)
    # print("Rephrased query:", complex_query)
    
    query_embedding = model.encode([complex_query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, k)
    results = []
    for rank, idx in enumerate(indices[0]):
        doc_name, para_idx = metadata[idx]
        results.append((doc_name, paragraphs[idx], distances[0][rank]))
    return results


# Integración del chat con la extracción de contexto de la base de datos
def rag_chat(index, metadata, paragraphs, query, prev_response, topic_model, model="llama3.2", url="http://kumo01:11434/api/chat"):
    global detected_language
    global similar_topics
    DISTANCE_THRESHOLD = 1.2

    topic_related = ""

    # Detectar lenguaje de la pregunta
    mult_doc = mult_nlp(query)

    # Traducir la pregunta a español porque la base de datos está en español
    detected_language = mult_doc._.language['language']

    if detected_language =='UNKNOWN':
        detected_language = 'es'

    if detected_language != 'es':
        query = GoogleTranslator(source=detected_language, target='es').translate(query)

    # Buscar párrafos relevantes
    relevant_paragraphs = query_similar_paragraphs(query, index, metadata, paragraphs)

    # Crear contexto para el modelo filtrando términos poco relevantes
    filtered_paragraphs = [(doc_name, para, distance) for doc_name, para, distance in relevant_paragraphs if distance < DISTANCE_THRESHOLD]
    context = "\n".join([f"From {doc_name}: {para}." for doc_name, para, distance in filtered_paragraphs])

    if not context:
        response = {"message": {"role": "assistant", "content": "No tengo suficiente información para proporcionar una respuesta precisa."}}

    else:
        prompt = f"Contexto: \n{context}\n\nPregunta: {query}. Recuerda SIEMPRE proporcionar las fuentes de donde obtienes la información para proporcionar la respuesta, escribiendo Según el Artículo X del BOE-A-YYYY-ZZZZZ (Boletín Oficial del Estado)."

        # Obtener respuesta del modelo
        response = chat_response(model, prompt=prompt, prev_response=prev_response, url=url)

        # Proponer sugerencias
        similar_topics = topic_model.find_topics(prompt, top_n=3)
        topic_info = topic_model.get_topic_info()
        topic_related = f"\nTambién puedes consultar los siguientes temas relacionados:\n"
        if len(similar_topics[0]) == 0:
            topic_related = ""
        for i in range(len(similar_topics[0])):
           # Obtener el nombre del tópico y eliminar números y guiones bajos
            topic_name = topic_info.loc[similar_topics[0][i]+1]['Name']  # Los tópicos empiezan en -1
            topic_name = re.sub(r'\d+', '', topic_name)  # Eliminar números
            topic_name = topic_name.replace('_', ' ')  # Eliminar guiones bajos
            
            # Imprimir el nombre del tema relacionado
            topic_related += f"\n{i+1}. {topic_name}"

        # Traducir la respuesta y la sugerencia de tópicos al idioma original en el que se hizo la pregunta
        if detected_language != "es":
            response['message']['content'] = GoogleTranslator(source='es', target=detected_language).translate(response['message']['content'])

            if topic_related != "":
                topic_related = GoogleTranslator(source='es', target=detected_language).translate(topic_related)

    return response, topic_related


def generate_summary(text, max_length=150, min_length=50):
    """Generar un resumen del texto proporcionado."""

    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)

    return summary[0]['summary_text']


# Bucle interactivo para el chat
if __name__ == "__main__":

    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    topic_model = BERTopic.load("topic_model.pkl")

    folder_path = "data"  # Carpeta con los documentos
    database_path = "database"
    index_path = os.path.join(database_path, "db.index")
    metadata_path = os.path.join(database_path, "metadata.json")

    print("Leyendo índice de la base de datos...")

    index_db = faiss.read_index(index_path)
    with open(metadata_path, 'r') as file:
        metadata = json.load(file)
    
    paragraphs =  [item['paragraph'] for item in metadata]
    metadata =  [(item['doc'], item['id']) for item in metadata]

    print("Hola soy BOEtiquin, tu asistente legal que responde preguntas de una base de datos documental del Boletín Oficial del Estado (BOE). ¿En qué puedo ayudarte hoy?")
    prev_response = {"content": ""}
    topic_selected = ""
    while True:
        if topic_selected != "":
            query = topic_selected
            query = GoogleTranslator(source='es', target=detected_language).translate(query)
        else:
            query = input("\nPregunta: ")

        if query.lower() in ["salir", "exit", "quit", "q"]:
            salir = "Saliendo del chat..."
            if detected_language != "es":
                salir = GoogleTranslator(source='es', target=detected_language).translate(salir)
            print(salir)
            break
        
        response, topic_related = rag_chat(index_db, metadata, paragraphs, query, prev_response, topic_model)
        print(f"\n{response['message']['content']}")

        if topic_related != "":
            print(f"{topic_related}")

        if len(word_tokenize(response['message']['content'])) >= MAX_TOKENS_RESPONSE:
            pregunta = "¿Quieres un resumen? Si/No"
            if detected_language != "es":
                pregunta = GoogleTranslator(source='es', target=detected_language).translate(pregunta)

            resumen = input(f"\n{pregunta} (1/0):\n>> ")
            if resumen.lower() == "si" or resumen.lower() == "yes" or resumen == "1":
                summary = generate_summary(response['message']['content'])
                print(f"\n{summary}")
        
        pregunta = "Quieres saber más sobre alguno de los temas relacionados? (Sí/no)"
        if detected_language != "es":
            pregunta = GoogleTranslator(source='es', target=detected_language).translate(pregunta)

        topic_question = input(f"\n{pregunta} (1/0):\n>> ")
        if topic_question.lower() == "si" or topic_question.lower() == "yes" or topic_question == "1":
            topic_string = "Sobre qué topic quieres más información?"
            if detected_language != "es":
                topic_string = GoogleTranslator(source='es', target=detected_language).translate(topic_string)
            while True:
                topic = input(f"\n{topic_string} (1/2/3):\n>> ")
        
                if topic in ["1", "2", "3"]:
                    topic_selected = topic_model.get_topic_info().loc[similar_topics[0][int(topic)-1]+1]['Name']
                    topic_selected = re.sub(r'\d+', '', topic_selected)  # Eliminar números
                    topic_selected = topic_selected.replace('_', ' ')  # Eliminar guiones bajos
                    break
        else:
            topic_selected = ""        
 
        prev_response = response['message']
