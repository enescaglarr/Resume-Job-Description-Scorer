from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import pickle
from constants import EMBEDDING_MODEL_NAME, GOOGLE_API_KEY, OUTPUT_PATH


class EmbeddingModel:
    """
    A class to handle the creation, saving, and reading of embeddings using Google's Gemini embedding model.
    """
    def __init__(self):
        """
        Initializes the EmbeddingModel with the specified Gemini embedding model and API key.
        """
        self.embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model=EMBEDDING_MODEL_NAME)

    def get_embeddings(self, data_dict):
        """
        Generates embeddings for the given data.

        Args:
            data_dict (dict): A dictionary where the keys are identifiers and the values are the texts to be embedded.

        Returns:
            dict: A dictionary with the same keys as the input and the corresponding embeddings as values.
        """
        output_dict = {}
        keys = list(data_dict.keys())
        values = list(data_dict.values())
        embeddings = self.embedding_model.embed_documents(values)
        for i in range(0, len(keys)):
            output_dict[keys[i]] = embeddings[i]
        return output_dict

    @staticmethod
    def save_embeddings(embedding, file_name):
        """
        Saves the given embeddings to a file.

        Args:
            embedding (dict): The embeddings to be saved.
            file_name (str): The name of the file to save the embeddings to.
        """
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        with open(OUTPUT_PATH + file_name, 'wb') as handle:
            pickle.dump(embedding, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def read_embeddings(file_name):
        """
        Reads embeddings from a file.

        Args:
            file_name (str): The name of the file to read the embeddings from.

        Returns:
            dict: The embeddings read from the file.
        """
        with open(OUTPUT_PATH + file_name, 'rb') as handle:
            output_dict = pickle.load(handle)
        return output_dict
