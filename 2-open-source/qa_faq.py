import requests
import streamlit as st

from tqdm.auto import tqdm
from elasticsearch import Elasticsearch
from openai import OpenAI


client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',
)

es_client = Elasticsearch('http://localhost:9200') 


def create_elastic_index(index_name="course-questions"):
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "section": {"type": "text"},
                "question": {"type": "text"},
                "course": {"type": "keyword"}
            }
        }
    }

    es_client.indices.create(index=index_name, body=index_settings)

    docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
    docs_response = requests.get(docs_url)
    documents_raw = docs_response.json()

    documents = []
    for course in documents_raw:
        course_name = course['course']

        for doc in course['documents']:
            doc['course'] = course_name
            documents.append(doc)

    for doc in tqdm(documents):
        es_client.index(index=index_name, document=doc)


def elastic_search(query, index_name="course-questions"):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "text", "section"],
                        "type": "best_fields"
                    }
                },
                "filter": {
                    "term": {
                        "course": "data-engineering-zoomcamp"
                    }
                }
            }
        }
    }

    response = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in response['hits']['hits']:
        result_docs.append(hit['_source'])
    
    return result_docs


def build_prompt(query, search_results):
    prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""
    
    for doc in search_results:
        context = context + f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['text']}\n\n"
    
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


def llm(prompt):
    response = client.chat.completions.create(
        model='phi3',
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


def rag(query, index_name):
    search_results = elastic_search(query, index_name=index_name)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer


def run_ui(index_name):
    st.title("RAG Function Invocation")

    user_input = st.text_input("Enter your input:")

    if st.button("Ask"):
        with st.spinner('Processing...'):
            output = rag(user_input, index_name)
            st.success("Completed!")
            st.write(output)


if __name__ == "__main__":
    index_name = "course-questions"
    if not es_client.indices.exists(index=index_name):
        create_elastic_index(index_name=index_name)

    run_ui(index_name)

# run:
# 1. docker-compose up          # spin up elasticsearch and ollama containers
# 2. streamlit run qa_faq.py    # run the streamlit UI
#   sample query: "I just discovered the course. Can I still join it?"
# 3. after shutting everything down, run "docker-compose down" to clean up docker containers
