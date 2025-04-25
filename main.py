from flask import Flask, request, jsonify, render_template,request,redirect,url_for,session
import csv
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import quizz
import numpy as np
from google import genai
import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from get_embedding_function import get_embedding_function
import wikipedia 
import requests
CHROMA_PATH = "chroma"

app = Flask(__name__)
global level
level = []
app.secret_key = 'supersecretkey' 
PROMPT_TEMPLATE = """
answer the question based on the folowing context, give a plenty of details, if the context dosent have the infomation asnswer it from your knowladge:

{context}

---

question is: {question}
"""
@app.route('/select', methods=['POST'])
def select():
	global level
	level.append(request.json.get('category'))
	print(f"User selected: {level}")
	return jsonify({'message': f'Category {level} received!'})

def gen_Q():
	global level
	qlist = []
	print(level)
	for i in range(4):
		result = quizz.generate(level[0])
		qlist.append([result])
	with open("questions.csv", "w", newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		for item in qlist:
			writer.writerow([item]) 
@app.route('/quiz')
def quiz():
	gen_Q()

	session['current_question'] = 0
	session['answers'] = []
	return redirect(url_for('question'))

@app.route('/question')
def question():
	qs = []
	with open("questions.csv", "r", newline='', encoding='utf-8') as f:
		reader = csv.reader(f)
		data = list(reader)
	
	for row in data:
		qs.append(row)
	quiz_questions = [
	{"question": qs[0]},
	{"question": qs[1]},
	{"question": qs[2]},
	{"question": qs[3]},
	]

		
	
	index = session.get('current_question', 0)
	if index < len(quiz_questions):
		question_text = quiz_questions[index]["question"]
		return render_template('quiz.html', question=question_text, number=index + 1)
	else:
		return redirect(url_for('results'))

@app.route('/submit', methods=['POST'])
def submit_answer():
	answer = request.form.get('answer')
	session['answers'].append(answer)
	with open("answers.csv", "w", newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		for items in session["answers"]:
			writer.writerow([answer]) 
	session['current_question'] += 1
	return redirect(url_for('question'))

@app.route('/results')
def results():
	PROMPT_TEMPLATE = """
check wether my answers are correct or wrong and explain them based on the context:

{context}

---

this is the list of questions and answers: {question}
"""
	global level
	ans = []
	with open("answers.csv", "r", newline='', encoding='utf-8') as f:
		reader = csv.reader(f)
		data = list(reader)
	
	for row in data:
		ans.append(row)
		
		
	qs = []
	with open("questions.csv", "r", newline='', encoding='utf-8') as f:
		reader = csv.reader(f)
		data = list(reader)
	
	for row in data:
		qs.append(row)
		
	print(qs,ans)
	query_text = str("question: ",qs[0],"answer: ",ans[0],"question: ", qs[1],"answer: ",ans[1],"question: ",qs[2],"answer: ",ans[2],"question: ",qs[3],"answer: ",ans[3])
	embedding_function = get_embedding_function()
	db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

	results = db.similarity_search_with_score(level, k=5)

	context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

	prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
	prompt = prompt_template.format(context=context_text, question=query_text)
	print(prompt)
    
	client = genai.Client(api_key="")
	response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
	print(response.text)		
	return render_template('results.html', qas=response.text)

@app.route("/selpage")
def selectpage():
	return render_template("select_sub.html")
	
@app.route('/')
def home():
	return render_template("index.html")
	
	
@app.route('/textbook')
def textbooks():
	return render_template("textbook.html")
@app.route('/chatwithme')	
def chat_page():
	return render_template("chat.html")

@app.route('/chat', methods=['POST'])
def chat():

	query_text = request.json.get('message')
	try:
		extra_info = wikipedia.summary(query_text, sentences= 5)
	except:
		extra_info = "no extra info"
		pass

	#parser = argparse.ArgumentParser()
	#parser.add_argument("query_text", type=str, help="The query text.")
	#args = parser.parse_args()
	#query_text = args.query_text
	
	
	print(query_text)
	embedding_function = get_embedding_function()
	db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

	results = db.similarity_search_with_score(query_text, k=5)

	context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
	context_text += "\n\n[Extra Info]\n\n" + extra_info
	#context_text += "\n\n[Extra Info]\n\n" + extra_info_web

	prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
	prompt = prompt_template.format(context=context_text, question=query_text)
	print(prompt)
    
	client = genai.Client(api_key="")
	response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
	print(response.text)
	return jsonify({'response': response.text})


if __name__ == '__main__':
    app.run(debug=True)
