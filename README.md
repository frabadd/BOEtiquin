# Bienvenido a BOEtiquin! 👋⚖️

Boetiquin es un chatbot que responde preguntas de una base de datos documental del Boletín Oficial del Estado (BOE), proporcionando respuestas fundamentadas y relevantes.

# 1. Funcionalidades

## Funciones básicas 🧩
El sistema implementa tres funcionalidades principales:

- BOEtiquin proporciona respuestas fundamentadas en los documentos del BOE, especificando siempre el documento y el artículo correspondiente.
- El chatbot está programado para no generar una respuesta en caso de que la base de datos no contenga un documento relevante.
- Detecta el idioma automáticamente, por tanto las respuestas están en el mismo idioma que la pregunta.


## Funciones adicionales ✨
Además de las funcionalidades principales, el sistema incorpora varias características adicionales que mejoran su rendimiento y usabilidad:

- Se ha integrado la versión de chat de Ollama 3.2, lo que permite mantener una conversación continua con el chatbot, en lugar de responder únicamente a una consultas.
- El sistema aplica un proceso de normalización y lematización a cada consulta para identificar los términos relevantes, facilitando la búsqueda precisa de documentos relacionados en la base de datos.
- BOEtiquin sugiere temas relacionados al responder, proporcionando un contexto adicional al usuario.
- Ofrece la opción de generar resúmenes automáticos de cada respuesta.
- El chatbot es capaz de manejar consultas en múltiples idiomas.

# 2. Implementación
## Dataset 🧾
El dataset utilizado está compuesto por:
- 107 documentos del Boletín Oficial del Estado (BOE) publicados entre 2010 y 2023.
- La Constitución Española de 1978.

Los documentos fueron preprocesados parapermitir la estructuración de los textos de manera uniforme, facilitando su integración en el sistema.

## Base de datos vectorial 🛢️

Para la construcción de la base de datos vectorial, se utilizó FAISS (Facebook AI Similarity Search),y para la generación de los embeddings se utilizó el modelo dariolopez/bge-m3-es-legal-tmp-6,
especializado en textos legales en español, lo que permitió capturar con precisión el significado de términos jurídicos y expresiones propias del ámbito legislativo.


La segmentación de los documentos en chunks se realizó en párrafos mediante dobles saltos de línea, aplicando solapamiento (overlap) parapreservar el contexto. Tras experimentar con distintos tamaños de contexto, se determinó que esta técnica mejoraba la continuidad y representación semántica, al incorporar información de los párrafos adyacentes, lo que optimizó la precisión de las respuestas del sistema.

## Modelos 🧠

Durante el desarrollo del proyecto, se combinaron diferentes modelos: 
- dariolopez/bge-m3-es-legal-tmp-6 para la obtenciónn de embeddings.
- ollama 3.2 en modalidad chat para interacción contextual.
- BERTopic para la sugerencia de tópicos.
- facebook/bart-large-cnn para resúmenes de la respuesta obtenida
- GoogleTranslator para soporte multilingÜe.



Para información adicional consultar la documentación.
