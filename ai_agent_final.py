from os import environ
from getpass import getpass
environ["OCTOAI_API_KEY"] = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjNkMjMzOTQ5In0.eyJzdWIiOiJjOTMwYzBkZC0zYzkyLTQyZDEtYTc1My1lN2ViNjgzOGU1MzIiLCJ0eXBlIjoidXNlckFjY2Vzc1Rva2VuIiwidGVuYW50SWQiOiJmMmRiOTI5Mi05NjM0LTQ1ZmEtYWUyOS05ODAyYTdkZWNkYzQiLCJ1c2VySWQiOiI3ZDk3ZTIzOS0xNzQzLTQ2MWUtYjRiOS05N2Q1YTAyNTYxNTEiLCJhcHBsaWNhdGlvbklkIjoiYTkyNmZlYmQtMjFlYS00ODdiLTg1ZjUtMzQ5NDA5N2VjODMzIiwicm9sZXMiOlsiRkVUQ0gtUk9MRVMtQlktQVBJIl0sInBlcm1pc3Npb25zIjpbIkZFVENILVBFUk1JU1NJT05TLUJZLUFQSSJdLCJhdWQiOiIzZDIzMzk0OS1hMmZiLTRhYjAtYjdlYy00NmY2MjU1YzUxMGUiLCJpc3MiOiJodHRwczovL2lkZW50aXR5Lm9jdG8uYWkiLCJpYXQiOjE3MjQ1MjE3NDZ9.MfKO6we42NX5vLGuVZwwCo46x4nT8BUX42gVGK3YcWZ3nLGye98hIgVC_p0cYelVRvg6yfxTXo--XL-0NJ3Nc3A6W9IvpiKZLhW9oBq2QzSGZxn3yK-0JqNANPqp6BRiV6V-dcu_XgL2fN3rVhkaDHJU-MIXRsnVxfESc1Ks2G_jpTDMmYRDSx3vNkoQzHTOJ5FsdVcdD33E6LzbHC_Q7hhlqUsaLgR-WwP4p6HchaQlo_2aTvCiLmG1xy8vZlcWJ-DmQoXU-BYuHubTyYhZ8gpeC3_nuqMgZW_pVPd-Y38EO9eewqlRfYLo8XZdLlqCYcCkbfHspfBjgKrn01tQIw"
from dotenv import load_dotenv

load_dotenv()

OCTOAI_API_KEY = environ["OCTOAI_API_KEY"]


from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.embeddings.octoai import OctoAIEmbedding
from llama_index.core import Settings as LlamaGlobalSettings
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai_like import OpenAILike

# Set the default model to use for embeddings
LlamaGlobalSettings.embed_model = OctoAIEmbedding()

# Create an llm object to use for the QueryEngine and the ReActAgent
llm = OpenAILike(
    model="meta-llama-3.1-70b-instruct",
    api_base="https://text.octoai.run/v1",
    api_key=environ["OCTOAI_API_KEY"],
    context_window=40000,
    is_function_calling_model=True,
    is_chat_model=True,
)


try:
    storage_context = StorageContext.from_defaults(
        persist_dir="./storage/msim_info"
    )
    msim_index = load_index_from_storage(storage_context)

    index_loaded = True
except:
    index_loaded = False

from llama_index.core.query_engine import CitationQueryEngine

import os
if not index_loaded:
    # load data
    msim_docs = SimpleDirectoryReader(
        input_files=["pdfs/"+ x for x in os.listdir("pdfs/")], filename_as_id = True).load_data()

    # build index
    msim_index = VectorStoreIndex.from_documents(msim_docs, show_progress=True)

    # persist index
    msim_index.storage_context.persist(persist_dir="./storage/msim_info")

    query_engine = CitationQueryEngine.from_args(
    msim_index,
    similarity_top_k=3,
    citation_chunk_size=1024,llm=llm
)
    

msim_engine = CitationQueryEngine.from_args(
    msim_index,
    similarity_top_k=3,
    citation_chunk_size=1024,llm=llm
)

query_engine_tools = [
    QueryEngineTool(
        query_engine=msim_engine,
        metadata=ToolMetadata(
            name="msim",
            description=(
                "Provides information about MSIM program "
                "Use a detailed plain text question as input to the tool."
            ),
        ),
    )
]

agent = ReActAgent.from_tools(
    query_engine_tools,
    llm=llm,
    max_turns=1,
)

import streamlit as st
st.title("UW Bot")
def get_output(inp):
    output = agent.chat(inp)
    print(str(output))
    return str(output)
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# React to user input
if prompt := st.chat_input("How can I help you?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    resp = f"UW Bot: {get_output(prompt)}"
    print(resp)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(resp)
    # Add assistant response to chat history
    st.session_state.messages.append({"role":"assistant", "content":resp})