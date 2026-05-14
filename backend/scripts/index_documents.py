import os
import glob
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("indexer")

def index_docs():
    '''
    Reads the PDFs, Chuncks them and upload them to azure search
    '''

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir,"../../backend/data")

    logger.info("="*60)
    logger.info("Environment Configuration Check:")
    logger.info(f"AZURE_OPENAI_ENDPOINT : {os.getenv("AZURE_OPENAI_ENDPOINT")}")
    logger.info(f"AZURE_OPENAI_API_VERSION : {os.getenv("AZURE_OPENAI_API_VERSION")}")
    logger.info(f"Embedding Deployment : {os.getenv("AZURE_OPENAI_EMBEDDINGDEPLOYMENT",'text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv("AZURE_SEARCH_ENDPOINT")}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv("AZURE_SEARCH_INDEX_NAME")}")
    logger.info("="*60)

    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required env variable: {missing_vars} ")
        logger.error("Please check .env file and ensure all the variables are set")
        return
    
    try:
        logger.info("Initalise the Azure OpenAI Embedding.......")
        embedding = AzureOpenAIEmbeddings(
            azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGDEPLOYMENT",'text-embedding-3-small'),
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION","2024-02-01")
        )
        logger.info("Embedding model initalised successfully")
    except Exception as e:
        logger.error(f"Failed to initalise embeddings :{e}")
        logger.error("Please verify Azure Openai deployment and endpoint")

    try:
        logger.info("Initalise the Azure AI SEARCH vector store.......")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        vector_store = AzureSearch(
            azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function = embedding.embed_query,
        )
        logger.info("Azure Search initalised successfully")
    except Exception as e:
        logger.error(f"Failed to initalise Azure Search :{e}")
        logger.error("Please verify Azure Search API KEY, index name  and endpoint")
        return
    
    pdf_files = glob.glob(os.path.join(data_folder,"*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {data_folder}. Please add files.")
    logger.info(f"Found {len(pdf_files)} PDFs to process : {[os.path.basename(f) for f in pdf_files]}")

    all_splits = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading: {os.path.basename(pdf_path)} ........")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chuck_size = 1000,
                chunk_overlap =200
            )
            splits = text_splitter.split_documents(raw_docs)
            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Split into {len(splits)} chunk.")

        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")


        if all_splits:
            logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search index {index_name}")
            try:
                vector_store.add_documents(documents = all_splits)
                logger.info("Indexing Complete! Knowledge base is ready......")
                logger.info(f"Total chuncks indexed: {len(all_splits)}")
                logger.info("="*60)

            except Exception as e:
                logger.error(f"Failed to upload the document to Azure Search: {e}")
                logger.error("Please check the Azure Search configuration and try again")
        else:
            logger.warning("No Document were processed")

if __name__ =="__main__":
    index_docs()
                




