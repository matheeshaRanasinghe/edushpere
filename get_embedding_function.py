from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_function():
	#init(project="edusphere-457813", location="us-central1")
	embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
	return embeddings
