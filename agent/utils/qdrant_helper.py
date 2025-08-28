import os
import json
from uuid import uuid4
import streamlit as st
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

QDRANT_KEY = st.secrets.get("QDRANT_KEY")
QDRANT_URL = st.secrets.get("QDRANT_URL")
COLLECTION_NAME = "diagram_generator"

def create_documents(folder):
    documents = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            service_name = os.path.splitext(os.path.basename(filename))[0]
            filepath = os.path.join(folder, filename)
            with open(filepath, "r") as file:
                try:
                    data = json.load(file)
                    for section, modules in data.items():
                        for module in modules:

                            metadata = {"module":module, "service": service_name, "section": section}

                            page_content = module.split(".")[-1]
                            document = Document(
                                page_content=page_content,
                                metadata=metadata
                            )
                            documents.append(document)

                            modules = module.split(".")
                            page_content = f"{modules[1]} {modules[-1]}"
                            document = Document(
                                page_content=page_content,
                                metadata=metadata
                            )
                            documents.append(document)

                except json.JSONDecodeError as e:
                    print(f"Error reading {filename}: {e}")
    return documents

class QdrantHandler:
    def __init__(self, embedding):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
        try:
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=COLLECTION_NAME,
                embedding=embedding,
            )
        except Exception as e:
            self.create_collection(COLLECTION_NAME, embedding_size=1536)
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=COLLECTION_NAME,
                embedding=embedding,
            )
    def create_collection(self, collection_name, embedding_size):
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
        )
        print(self.get_collections())

    def delete_collection(self, collection_name):
        self.client.delete_collection(collection_name=collection_name)

    def get_collections(self):
        return self.client.get_collections()

    def add_documents(self, documents):
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self.vector_store.add_documents(documents=documents, ids=uuids)

    def query(self, query_text, service_name=None, score_min=0, k=3):
        #filter = models.Filter(
        #    must=[
        #        models.FieldCondition(
        #            key="service",
        #            match=models.MatchValue(value=service_name),
        #        )
        #    ]
        #)
        results = self.vector_store.similarity_search_with_score(
            query_text, k=k,
            #filter=filter
        )
        filtered_docs = []
        for doc, score in results:
            if score >= score_min:
                filtered_docs.append(doc.metadata["module"])
                #print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")
        return "\n".join(filtered_docs)

if __name__ == "__main__":
    API_KEY = st.secrets.get("OPENAI_KEY")
    EMBEDDING_MODEL = st.secrets.get("OPENAI_EMBEDDING_MODEL")
    EMBEDDING_SIZE = st.secrets.get("OPENAI_EMBEDDING_SIZE")

    embedding = OpenAIEmbeddings(api_key=API_KEY, model=EMBEDDING_MODEL)
    qdrant_handler = QdrantHandler(embedding=embedding)
    
    ingest = False
    if ingest is True:    
        #qdrant_handler.delete_collection(COLLECTION_NAME)
        documents = create_documents(folder="D:\\python_scripts\\git_repo\\diagram_generator\\services")
        qdrant_handler.add_documents(documents[:])

    text = "aws api gateway"
    results = qdrant_handler.query(text)
    print(results)