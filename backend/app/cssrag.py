import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
import shutil

load_dotenv()

# Set the OpenAI API key

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Setting file paths for CSS storage and vector store

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "raw_css"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORE_DIR = BASE_DIR / "css_chunks"

#Initialize the OpenAI embeddings

EMBEDDINGS = OpenAIEmbeddings()

# Function to save CSS content to a file based on the URL

def save_css_file(css_content, url):
    if not url:
        return {"error": "No URL provided"}

    if not css_content:
        return {"error": "No CSS content provided"}

    hostname = url.split("//")[-1].split("/")[0].replace("www.", "")
    filename = f"{hostname}.css"
    file_path = DATA_DIR / filename

    try:
        if isinstance(css_content, list):
            css_content = "\n\n".join(css_content)
        else:
            css_content = str(css_content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(css_content)
        return {"message": f"CSS content saved to {file_path}"}
    except Exception as e:
        return {"error": str(e)}

# Function to get or create a vector store for the CSS file based on the URL

def get_vectorstore_for_css_file(url):
    hostname = url.split("//")[-1].split("/")[0].replace("www.", "")
    filename = f"{hostname}.css"
    file_path = DATA_DIR / filename
    
    # Check if the CSS file exists

    storing_dir = STORE_DIR / hostname
    storing_dir.mkdir(parents=True, exist_ok=True)

    if not any(storing_dir.iterdir()):
        with open(file_path, 'r', encoding='utf-8') as file:
            css_content = file.read()

        # Split the CSS content into chunks for vectorization

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(css_content)

        documents = [Document(page_content=chunk) for chunk in chunks]

        # Create a new vector store with the CSS chunks

        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=EMBEDDINGS, 
            persist_directory=str(storing_dir),
            collection_name=hostname
        )
        
    else:

        # If the vector store already exists, load it

        vector_store = Chroma(
            embedding_function=EMBEDDINGS,
            persist_directory=str(storing_dir),
            collection_name=hostname
        )
    return vector_store

def get_llm_answer_for_css(query, url):
    if not query:
        return {"error": "No query provided"}
    
    # Perform a similarity search on the vector store for the CSS file

    vector_store = get_vectorstore_for_css_file(url)
    docs = vector_store.similarity_search(query, k=1)
    
    # Initializing the base prompt for the LLM

    base_prompt = """For the provided CSS selector output the singular CLOSEST matching style block

    Rules:
    1. Only output the CSS block that matches the selector.
    2. Do not output any additional text or explanations.
    3. The output should be a singular valid CSS block enclosed in braces.
    4. If multiple style blocks match the selector, return the one that is most relevant to the query.
    5. IMPORTANT: If a style block has a field with "--" in it, INTERPRET it to the CLOSEST normal CSS value that you know. 

    Example for Rule 5: "--sds-c-button-border-width:2px" should be interpreted as "border-width:2px".

    Here is the CSS selector: {query}
    Here is the content from the CSS file: {docs}"""

    prompt = base_prompt.format(
        query=query,
        docs=docs
    )

    # Initialize the LLM with the specified model and temperature, prompt it and return an answer

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    response = llm.invoke(prompt)

    return {"answer": response.content}

# Function to clean up the CSS data directory

def remove_css_dirs():
    try:
        # Delete raw_css directory
        if DATA_DIR.exists() and DATA_DIR.is_dir():
            shutil.rmtree(DATA_DIR)

        # Delete css_chunks directory
        if STORE_DIR.exists() and STORE_DIR.is_dir():
            shutil.rmtree(STORE_DIR)

        return {"message": "Successfully removed raw_css and css_chunks directories."}
    except Exception as e:
        return {"error": str(e)}