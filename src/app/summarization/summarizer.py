# src/app/summarization/summarizer.py
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from app.core.config import settings

def summarize_chunks(chunks):
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name="gpt-4o",
        temperature=0
    )
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    return chain.run(chunks)