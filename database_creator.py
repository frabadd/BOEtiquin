import json
import os

import faiss
from sentence_transformers import SentenceTransformer

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


# Leer múltiples documentos y añadir context-overlap
def load_and_split_texts(folder_path, context_size=0):
    documents = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            split_paragraphs = [para.strip() for para in text.split('\n\n') if para.strip()]

            paragraphs = []
            if context_size > 0:
                for i, para in enumerate(split_paragraphs):
                    # Obtener el contexto anterior y posterior
                    previous_context = split_paragraphs[i - 1][-context_size:] if i > 0 else ""
                    next_context = split_paragraphs[i + 1][:context_size] if i < len(split_paragraphs) - 1 else ""

                    # Combinar el párrafo actual con el contexto
                    combined_para = f"{previous_context}{para}{next_context}"
                    paragraphs.append(combined_para)
            else:
                paragraphs = split_paragraphs

            documents[file_name] = paragraphs

    return documents


# Generar embeddings para los documentos
def generate_embeddings(documents, model_name):
    model = SentenceTransformer(model_name, device = 'cuda')
    metadata, paragraphs= [], []
    
    for doc_name, paras in documents.items():
        for i, para in enumerate(paras):
            paragraphs.append(para)
            metadata.append({
                "id": i,
                "paragraph": para,
                "doc": doc_name
            })
    embeddings = model.encode(paragraphs, convert_to_numpy=True)
    return embeddings, metadata


# Construir índice FAISS
def build_faiss_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index



MODEL_NAME = "dariolopez/bge-m3-es-legal-tmp-6"
CONTEXT_SIZES = [0, 25, 50, 75, 100, 150]

for context_size in CONTEXT_SIZES:
    folder_path = "data/documentos_boe_txt"
    database_path = "database/" + MODEL_NAME + "_" + str(context_size)

    index_path = os.path.join(database_path, "db.index")
    metadata_path = os.path.join(database_path, "metadata.json")

    print("Cargando documentos ...")
    documents = load_and_split_texts(folder_path, context_size=context_size)

    print("Generando embeddings ...")
    embeddings, metadata = generate_embeddings(documents, model_name=MODEL_NAME)

    print("Construyendo índice FAISS ...")
    index = build_faiss_index(embeddings)

    print("Guardando la base de datos ...")
    if not os.path.exists(database_path):
        os.makedirs(database_path, exist_ok=True)
    faiss.write_index(index, index_path)

    # Guardar los metadatos en un archivo JSON
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    print("Base de datos construida y guardada en ", database_path)
