from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import json
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import re

if __name__ == "__main__":
    folder_path = "data"  # Carpeta con los documentos
    database_path = "database_dariolopez/bge-m3-es-legal-tmp-6_100" 
    load = False
    if load:
        topic_model = BERTopic.load("topic_model.pkl")
    else:
        # Modelo preentrenado para embeddings
        embedding_model = SentenceTransformer('dariolopez/bge-m3-es-legal-tmp-6', device='cuda')
        metadata_path = os.path.join(database_path, "metadata.json")
        with open(metadata_path, 'r') as file:
                metadata = json.load(file)
        
        my_corpus = [doc['paragraph'] for doc in metadata]
        my_corpus = [re.sub(r'\d+', '', para) for para in my_corpus]  # Eliminar números

        # Inicializar BERTopic con el modelo de embeddings
        vectorizer_model = CountVectorizer(stop_words=stopwords.words('spanish'))
        topic_model = BERTopic(embedding_model=embedding_model, language="spanish", nr_topics=50, vectorizer_model= vectorizer_model, umap_model=UMAP(low_memory=True))

        # Obtener los temas de la respuesta
        topics, probs = topic_model.fit_transform(my_corpus)

    # Mostrar los temas descubiertos
    topic_info = topic_model.get_topic_info()
    print(topic_info)

    response = """Pregunta: ¿Cuáles son las funciones del presidente del gobierno?. """

    similar_topics = topic_model.find_topics(response, top_n=3)
    print("Temas relacionados:", similar_topics)
    for i in range(3):
        print("Tema", i, ":", topic_info.loc[similar_topics[0][i]]['Name'])
    
    if load != True:
        topic_model.save("topic_model.pkl")
        print("Modelo guardado")


# # Usar un modelo más avanzado
# embedding_model = SentenceTransformer('all-mpnet-base-v2')
# topic_model = BERTopic(embedding_model=embedding_model)


# similar_topics = topic_model.find_topics(response[0], top_n=3)
# print("Temas relacionados:", similar_topics)
