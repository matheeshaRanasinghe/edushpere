from google import genai
import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from get_embedding_function import get_embedding_function
CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
generate a question based only on the following context:

{context}

---

generate a question based on the above context: {question}
"""



def generate(query_text: str):
	embedding_function = get_embedding_function()
	db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

	results = db.similarity_search_with_score(query_text, k=3)

	context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
	prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
	prompt = prompt_template.format(context=context_text, question=query_text)
	print(prompt)
    
	client = genai.Client(api_key="")
	response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
	
	return response.text








