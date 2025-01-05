import gdown
import os
import sys


if sys.version_info < (3, 10):
    # Código para versiones 3.10 o anteriores
    url_topic_model = 'https://drive.google.com/uc?export=download&id=d/1gFLnbgEwPe70XAnoihZvCTrDGBXpsWpL'
else:
    # Código para versiones 3.11 o posteriores
    url_topic_model = 'https://drive.google.com/uc?export=download&id=13ZgZGjwbLkBNnCbZQs3mtz-3zqHCbk1S'

output_topic_model = 'topic_model.pkl'
gdown.download(url_topic_model, output_topic_model, quiet=False)

os.makedirs('database', exist_ok=True)
output_db_index = 'database/db.index'
url_db_index = 'https://drive.google.com/uc?export=download&id=1wCbvc7A2P8SmMIvLMNfiySaxtt5I72bA'
gdown.download(url_db_index, output_db_index, quiet=False)

output_db_metadata = 'database/metadata.json'
url_db_metadata = 'https://drive.google.com/uc?export=download&id=1XI5gJN5Lx4G2nOBQ6UMIrqqi-nhskYBp'
gdown.download(url_db_metadata, output_db_metadata, quiet=False)
