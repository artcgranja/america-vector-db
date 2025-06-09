# src/app/summarization/summarizer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain

def summarize_file(file_text: str):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        temperature=0
    )
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    return chain.run(file_text)