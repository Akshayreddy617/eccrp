"""
ECCRP AI/RAG Engine
Module 12 - AI Governance Assistant using LangChain + OpenSearch RAG.
"""

from typing import Optional, List, Dict, Any
import time
import structlog

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Indian election law compliance assistant for the
Election Compliance & Candidate Readiness Platform (ECCRP).

You assist candidates, consultants, lawyers, and journalists with questions about:
- Election eligibility under the Constitution of India
- Representation of the People Act 1950 and 1951
- Conduct of Election Rules 1961
- Election Commission of India guidelines and circulars
- Model Code of Conduct
- Supreme Court judgments related to elections
- Affidavit and disclosure obligations
- Election expenditure rules

CRITICAL INSTRUCTIONS:
1. Always cite the specific legal provision (Article, Section, Rule number).
2. Always reference the most relevant Supreme Court judgment.
3. Do NOT provide personal legal advice — always recommend consulting a qualified lawyer for specific cases.
4. If uncertain, say so clearly — never fabricate legal provisions.
5. Provide a confidence score between 0 and 1.
6. Structure your response with: Answer | Legal Basis | Relevant Judgment | Recommended Action.
7. Respond in clear, plain English that a non-lawyer can understand.

CONTEXT FROM LEGAL KNOWLEDGE BASE:
{context}

Always end with the disclaimer that this is for informational purposes only and does not constitute legal advice."""

QUERY_REWRITE_PROMPT = """Rewrite the following election law query to be more precise 
for legal document retrieval. Keep the Indian legal context. Return only the rewritten query.

Original query: {query}
Rewritten query:"""


class ECCRPRagEngine:
    """RAG engine for the AI Governance Assistant."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self._opensearch_client = None

    def _get_opensearch_client(self):
        if self._opensearch_client is None:
            from opensearchpy import AsyncOpenSearch
            self._opensearch_client = AsyncOpenSearch(
                hosts=[settings.OPENSEARCH_URL],
                http_auth=(settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)
                if settings.OPENSEARCH_USERNAME else None,
            )
        return self._opensearch_client

    async def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better retrieval."""
        try:
            prompt = QUERY_REWRITE_PROMPT.format(query=query)
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception:
            return query

    async def _retrieve_context(
        self, query: str, election_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant legal documents from OpenSearch."""
        try:
            # Generate embedding for semantic search
            query_embedding = await self.embeddings.aembed_query(query)

            client = self._get_opensearch_client()

            # Build filter
            filter_clause = []
            if election_type:
                filter_clause.append({
                    "terms": {"applicable_election_types": [election_type]}
                })

            # Hybrid search: semantic + keyword
            search_body = {
                "size": settings.RAG_TOP_K,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "knn": {
                                    "embedding_vector": {
                                        "vector": query_embedding,
                                        "k": settings.RAG_TOP_K,
                                    }
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^3", "full_text^2", "summary^2", "keywords"],
                                    "type": "best_fields",
                                }
                            },
                        ],
                        "filter": filter_clause,
                        "minimum_should_match": 1,
                    }
                },
                "_source": ["title", "section_number", "source_type", "summary", "full_text", "keywords"],
            }

            # Search across legal corpus indices
            results = []
            for index in [
                settings.OPENSEARCH_INDEX_LAWS,
                settings.OPENSEARCH_INDEX_JUDGMENTS,
                settings.OPENSEARCH_INDEX_KNOWLEDGE,
            ]:
                try:
                    resp = await client.search(index=index, body=search_body)
                    for hit in resp["hits"]["hits"]:
                        if hit["_score"] >= settings.RAG_SIMILARITY_THRESHOLD:
                            results.append({
                                "score": hit["_score"],
                                "source": hit["_source"],
                                "index": index,
                                "doc_id": hit["_id"],
                            })
                except Exception as e:
                    logger.warning("opensearch_index_search_failed", index=index, error=str(e))

            # Sort by score and deduplicate
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:settings.RAG_TOP_K]

        except Exception as e:
            logger.error("rag_retrieval_failed", error=str(e))
            return []

    def _format_context(self, retrieved_docs: List[Dict]) -> str:
        """Format retrieved documents as context for LLM."""
        if not retrieved_docs:
            return "No specific legal provisions retrieved. Answering from general knowledge."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc["source"]
            context_parts.append(
                f"[{i}] {source.get('source_type', 'Legal Document').upper()}\n"
                f"Section/Article: {source.get('section_number', 'N/A')}\n"
                f"Title: {source.get('title', '')}\n"
                f"Content: {source.get('summary') or source.get('full_text', '')[:500]}"
            )
        return "\n\n---\n\n".join(context_parts)

    def _build_citations(self, retrieved_docs: List[Dict]) -> List[Dict]:
        """Build citation list from retrieved documents."""
        citations = []
        for doc in retrieved_docs:
            source = doc["source"]
            citations.append({
                "source_type": source.get("source_type"),
                "section_number": source.get("section_number"),
                "title": source.get("title"),
                "relevance_score": round(doc["score"], 3),
                "document_id": doc["doc_id"],
            })
        return citations

    def _extract_judgments(self, retrieved_docs: List[Dict]) -> List[Dict]:
        """Extract judgment references from retrieved docs."""
        judgments = []
        for doc in retrieved_docs:
            if doc["index"] == settings.OPENSEARCH_INDEX_JUDGMENTS:
                source = doc["source"]
                judgments.append({
                    "case_name": source.get("title"),
                    "citation": source.get("section_number"),  # citation stored in section field
                    "relevance": source.get("summary", "")[:200],
                })
        return judgments

    def _calculate_confidence(self, retrieved_docs: List[Dict], response: str) -> float:
        """Estimate confidence score based on retrieval quality."""
        if not retrieved_docs:
            return 0.4  # Low confidence without retrieval

        top_score = retrieved_docs[0]["score"] if retrieved_docs else 0
        doc_count = len(retrieved_docs)

        # Higher confidence if we have high-scoring, multiple relevant docs
        base = min(top_score / 10.0, 1.0)  # Normalize score
        doc_factor = min(doc_count / settings.RAG_TOP_K, 1.0)
        confidence = (base * 0.7) + (doc_factor * 0.3)

        # Penalize if response contains uncertainty markers
        uncertainty_phrases = ["i'm not sure", "i cannot", "unclear", "may not be accurate"]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            confidence *= 0.7

        return round(min(max(confidence, 0.1), 1.0), 2)

    async def answer(
        self,
        query: str,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main RAG pipeline: retrieve → augment → generate."""
        start_time = time.perf_counter()

        election_type = context.get("election_type") if context else None

        # Step 1: Query rewrite for better retrieval
        rewritten_query = await self._rewrite_query(query)
        logger.info("rag_query_rewritten", original=query, rewritten=rewritten_query)

        # Step 2: Retrieve relevant documents
        retrieved_docs = await self._retrieve_context(rewritten_query, election_type)
        logger.info("rag_docs_retrieved", count=len(retrieved_docs))

        # Step 3: Format context
        context_text = self._format_context(retrieved_docs)

        # Step 4: Build prompt and generate response
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{query}"),
        ])

        messages = prompt.format_messages(context=context_text, query=query)

        response = await self.llm.ainvoke(messages)
        answer_text = response.content

        # Step 5: Build output
        citations = self._build_citations(retrieved_docs)
        judgments = self._extract_judgments(retrieved_docs)
        confidence = self._calculate_confidence(retrieved_docs, answer_text)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info("rag_response_generated", latency_ms=latency_ms, confidence=confidence)

        # Extract recommended action from response (basic parsing)
        recommended_action = None
        if "recommended action" in answer_text.lower():
            lines = answer_text.split("\n")
            for i, line in enumerate(lines):
                if "recommended action" in line.lower() and i + 1 < len(lines):
                    recommended_action = lines[i + 1].strip()
                    break

        return {
            "query": query,
            "answer": answer_text,
            "legal_basis": citations[:5],  # Top 5 legal citations
            "relevant_judgments": judgments[:3],  # Top 3 judgments
            "recommended_action": recommended_action,
            "confidence_score": confidence,
            "sources": citations,
            "latency_ms": latency_ms,
            "disclaimer": (
                "This answer is generated by an AI system for informational purposes only. "
                "It does not constitute legal advice. Consult a qualified election law practitioner "
                "for specific legal guidance."
            ),
        }


# ── Document Ingestion Pipeline ───────────────────────────────────────────────

class LegalDocumentIngester:
    """Ingests legal documents into OpenSearch for RAG retrieval."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " "],
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    async def ingest_legal_rule(self, rule: Dict[str, Any], index: str) -> str:
        """Ingest a legal rule/section into OpenSearch."""
        from opensearchpy import AsyncOpenSearch
        client = AsyncOpenSearch(hosts=[settings.OPENSEARCH_URL])

        # Combine text for embedding
        text = f"{rule.get('title', '')} {rule.get('summary', '')} {rule.get('full_text', '')}"
        chunks = self.text_splitter.split_text(text)

        # Generate embedding for first chunk (primary representation)
        embedding = await self.embeddings.aembed_query(text[:2000])

        doc = {
            "title": rule.get("title"),
            "section_number": rule.get("section_number"),
            "source_type": rule.get("source_type"),
            "summary": rule.get("summary"),
            "full_text": rule.get("full_text", "")[:5000],  # Truncate for storage
            "keywords": rule.get("keywords", []),
            "applicable_election_types": rule.get("applicable_election_types", []),
            "embedding_vector": embedding,
            "chunk_count": len(chunks),
        }

        resp = await client.index(index=index, body=doc)
        doc_id = resp["_id"]
        logger.info("legal_rule_ingested", doc_id=doc_id, title=rule.get("title"))
        return doc_id

    async def create_indices(self):
        """Create OpenSearch indices with KNN mapping."""
        from opensearchpy import AsyncOpenSearch
        client = AsyncOpenSearch(hosts=[settings.OPENSEARCH_URL])

        index_mapping = {
            "settings": {
                "index": {"knn": True, "knn.algo_param.ef_search": 100},
                "number_of_shards": 2,
                "number_of_replicas": 1,
            },
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "standard"},
                    "section_number": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "full_text": {"type": "text"},
                    "keywords": {"type": "keyword"},
                    "applicable_election_types": {"type": "keyword"},
                    "embedding_vector": {
                        "type": "knn_vector",
                        "dimension": settings.EMBEDDING_DIMENSIONS,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                        },
                    },
                }
            },
        }

        for index in [
            settings.OPENSEARCH_INDEX_LAWS,
            settings.OPENSEARCH_INDEX_JUDGMENTS,
            settings.OPENSEARCH_INDEX_KNOWLEDGE,
        ]:
            try:
                exists = await client.indices.exists(index=index)
                if not exists:
                    await client.indices.create(index=index, body=index_mapping)
                    logger.info("opensearch_index_created", index=index)
            except Exception as e:
                logger.error("opensearch_index_creation_failed", index=index, error=str(e))
