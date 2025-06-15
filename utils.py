import os
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import logging
from pymilvus import MilvusClient, utility, DataType, CollectionSchema, FieldSchema
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import uuid
import streamlit as st

# Setup logging with reduced verbosity
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize OpenAI client (now using Novita AI)
openai_client = OpenAI(
    api_key=st.secrets["NOVITA_API_KEY"],
    base_url=os.getenv("NOVITA_BASE_URL", "https://api.novita.ai/v3/openai")
)

# Model configurations
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek/deepseek-v3-0324")
EMBEDDING_DIMENSIONS = 4096  # Qwen3 embedding dimensions
COLLECTION_NAME = "contract_clauses_novita"

# Initialize Milvus client
CLUSTER_ENDPOINT = os.getenv("ZILLIZ_URI", "controller.api.gcp-us-west1.zillizcloud.com:19540")
TOKEN = os.getenv("ZILLIZ_API_KEY")

if not TOKEN:
    raise ValueError("""
    ZILLIZ_API_KEY must be set in .env file.
    
    To get this value:
    1. Go to https://cloud.zilliz.com
    2. Click on your cluster
    3. Go to 'Security' or 'API Keys' section to create an API key
    4. Add to your .env file:
       ZILLIZ_API_KEY=your-api-key
    """)

client = MilvusClient(
    uri=CLUSTER_ENDPOINT,
    token=TOKEN
)

def init_zilliz():
    """Initialize Milvus connection and create collection if it doesn't exist."""
    try:
        
        # Check if collection exists
        collections = client.list_collections()
        
        if COLLECTION_NAME not in collections:
            logger.info(f"Creating new collection: {COLLECTION_NAME}")
            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                FieldSchema(name="contract_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIMENSIONS)
            ]
            schema = CollectionSchema(fields=fields)
            
            # Create collection
            client.create_collection(
                collection_name=COLLECTION_NAME,
                schema=schema
            )
            logger.info("Collection created successfully")
            
        else:
            logger.info("Collection already exists")
        
        # Try to create index if it doesn't exist, but don't fail if it doesn't work
        try:
            indexes = client.list_indexes(collection_name=COLLECTION_NAME)
            if not indexes or "embedding" not in str(indexes):
                logger.info("Attempting to create index...")
                # Try the simplest index creation possible
                try:
                    # Connect using the traditional method for index creation
                    connections.connect(
                        alias="default",
                        uri=CLUSTER_ENDPOINT,
                        token=TOKEN
                    )
                    
                    # Get collection and create index
                    collection = Collection(COLLECTION_NAME)
                    collection.create_index(
                        field_name="embedding",
                        index_params={
                            "metric_type": "L2",
                            "index_type": "IVF_FLAT",
                            "params": {"nlist": 128}
                        }
                    )
                    logger.info("Index created successfully using traditional method")
                    
                except Exception as traditional_error:
                    logger.warning(f"Traditional index creation failed: {traditional_error}")
                    logger.info("Proceeding without index - will create during first search if needed")
            else:
                logger.info("Index already exists")
        except Exception as index_check_error:
            logger.warning(f"Could not check/create index: {index_check_error}")
            logger.info("Proceeding without index - collection can still be used")
        
        # Load collection to make it available for search
        try:
            client.load_collection(collection_name=COLLECTION_NAME)
            logger.info("Collection loaded successfully")
        except Exception as load_error:
            logger.warning(f"Collection load issue (will try again during search): {load_error}")
            
    except Exception as e:
        logger.error(f"Error initializing Milvus: {str(e)}")
        raise

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI's API."""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        raise

def store_clauses(contract_id: str, clauses: List[str]):
    """Store contract clauses in Milvus."""
    try:
        # Get embeddings for all clauses
        embeddings = [get_embedding(clause) for clause in clauses]
        
        # Prepare data for insertion
        data = []
        for i, (clause, embedding) in enumerate(zip(clauses, embeddings)):
            # Generate unique ID to avoid conflicts
            unique_id = int(str(uuid.uuid4().int)[:18])  # Use first 18 digits of UUID as int
            data.append({
                "id": unique_id,
                "contract_id": contract_id,
                "text": clause,
                "embedding": embedding
            })
        
        # Insert data
        client.insert(
            collection_name=COLLECTION_NAME,
            data=data
        )
        logger.info(f"Successfully stored {len(clauses)} clauses for contract {contract_id}")
    except Exception as e:
        logger.error(f"Error storing clauses: {str(e)}")
        raise

def search_similar_clauses(query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """Search for similar clauses using the query."""
    try:
        from pymilvus import connections, Collection
        
        logger.info(f"Searching for query: '{query}' with top_k={top_k}")
        
        # Connect using traditional method
        connections.connect(
            alias="search_connection",
            uri=CLUSTER_ENDPOINT,
            token=TOKEN
        )
        
        # Get collection and load it
        collection = Collection(COLLECTION_NAME, using="search_connection")
        collection.load()
        
        # Get query embedding
        logger.debug("Getting query embedding...")
        query_embedding = get_embedding(query)
        logger.debug(f"Query embedding generated, length: {len(query_embedding)}")
        
        # Search using traditional method
        logger.debug("Performing vector search...")
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "contract_id"]
        )
        
        logger.debug(f"Search completed, results type: {type(results)}")
        
        # Format results
        formatted_results = []
        if results and len(results) > 0:
            logger.debug(f"Processing {len(results[0])} search results")
            for i, hit in enumerate(results[0]):
                text = hit.entity.text if hasattr(hit.entity, 'text') else None
                distance = hit.distance
                
                if text and len(text.strip()) > 0:
                    formatted_results.append((text, distance))
                    logger.debug(f"Added result {i}: distance={distance:.4f}, text_preview='{text[:100]}...'")
        else:
            logger.warning("No search results returned")
        
        logger.info(f"Found {len(formatted_results)} similar clauses")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching similar clauses: {str(e)}", exc_info=True)
        # Return empty results instead of raising exception
        return []

def generate_response(query: str, context: List[str]) -> str:
    """Generate a response using OpenAI's API."""
    try:
        logger.info(f"Generating response for query: '{query}' with {len(context)} context items")
        
        if context and len(context) > 0:
            # We have relevant contract clauses
            context_text = '\n'.join([f"- {clause}" for clause in context])
            prompt = f"""You are ContractIQ, an AI assistant specialized in contract analysis. You have access to the user's uploaded contract document.

**Relevant Contract Information:**
{context_text}

**User Question:** {query}

**Instructions:**
- Answer directly and naturally as if you're reading from the contract document
- Use phrases like "The contract states...", "This document shows...", "According to the agreement..."
- Quote specific parts when relevant, but integrate them naturally into your response
- Be conversational and helpful, not robotic
- Focus on practical implications for the user
- Avoid saying "based on provided clauses" - instead speak as if you're directly analyzing their contract

**Answer:**"""
        else:
            # No specific context found, but still try to be helpful about contracts
            prompt = f"""You are ContractIQ, an AI assistant specialized in contract analysis. The user has uploaded a contract document, but I couldn't find specific information that directly relates to their question in the document.

**User Question:** {query}

**Instructions:**
- Acknowledge that you couldn't find specific information in their uploaded contract
- Provide general guidance about this topic in contract contexts
- Suggest what clauses or sections they should look for in their contract
- Be helpful and educational about contract terms
- Encourage them to ask more specific questions or rephrase their query
- Be conversational and natural, not robotic

**Answer:**"""

        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are ContractIQ, a specialized AI assistant for contract analysis. You help users understand their contracts by providing clear, accurate, and actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent responses
            max_tokens=500
        )
        
        generated_response = response.choices[0].message.content
        logger.info(f"Generated response length: {len(generated_response)}")
        return generated_response
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return "I apologize, but I'm having trouble processing your request right now. Please try asking your question again, or try rephrasing it." 