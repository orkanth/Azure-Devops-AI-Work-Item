
from uuid import UUID
import re
import psycopg
from psycopg.types.json import Jsonb

from app.core.config import settings


class KnowledgeRepository:

    EMBEDDING_DIMENSIONS = 1536

    def _get_connection(self):
        return psycopg.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_username,
            password=settings.db_password,
            dbname=settings.db_database,
        )

    def save_chunks(self, chunks: list[dict]) -> int:
        """
        Save document chunks and embeddings in one transaction.

        Existing chunks for the same document are replaced
        only when the complete operation succeeds.
        """

        if not chunks:
            raise ValueError("Cannot save an empty chunk list.")

        first_chunk = chunks[0]

        document_id = str(UUID(first_chunk["document_id"]))
        project_id = first_chunk["project_id"]

        if not project_id.strip():
            raise ValueError("Project ID is required.")

        # Validate all chunks before opening the transaction.
        for chunk in chunks:
            if str(UUID(chunk["document_id"])) != document_id:
                raise ValueError("Chunks contain different document IDs.")

            if chunk["project_id"] != project_id:
                raise ValueError("Chunks contain different project IDs.")

            if len(chunk["embedding"]) != self.EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Expected {self.EMBEDDING_DIMENSIONS} embedding "
                    f"dimensions, got {len(chunk['embedding'])}."
                )

        with self._get_connection() as connection:
            with connection.cursor() as cursor:

                # Prepare the search query
                terms = re.findall(r"[a-zA-Z0-9]+", query.lower())

                stop_words = {
                    "what", "are", "is", "the", "during",
                    "a", "an", "of", "should", "does"
                }

                search_query = " | ".join(
                    term for term in terms
                    if term not in stop_words
                )

                if not search_query:
                    return []

                # Execute SQL while cursor is available
                cursor.execute(
                    """
                    SELECT
                        kc.document_id,
                        kc.project_id,
                        d.file_name,
                        kc.content,
                        kc.chunk_index,
                        kc.page_number,
                        kc.metadata,
                        ts_rank_cd(
                            to_tsvector(
                                'simple',
                                replace(kc.content, '/', ' ')
                            ),
                            to_tsquery('simple', %s)
                        ) AS keyword_score
                    FROM knowledge_chunks kc
                    JOIN documents d
                        ON d.id = kc.document_id
                    WHERE kc.project_id = %s
                    AND to_tsvector(
                        'simple',
                        replace(kc.content, '/', ' ')
                    ) @@ to_tsquery('simple', %s)
                    ORDER BY keyword_score DESC
                    LIMIT %s
                    """,
                    (
                        search_query,
                        project_id,
                        search_query,
                        limit,
                    ),
                )

                rows = cursor.fetchall()
    
    
    
    def search_similar_chunks(
        self,
        query_embedding: list[float],
        project_id: str,
        limit: int = 5,
    ) -> list[dict]:

        if len(query_embedding) != self.EMBEDDING_DIMENSIONS:
            raise ValueError("Invalid query embedding dimensions.")

        if not project_id or not project_id.strip():
            raise ValueError("Project ID is required.")

        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50.")

        embedding = "[" + ",".join(
            str(float(value)) for value in query_embedding
        ) + "]"

        with self._get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        kc.document_id,
                        kc.project_id,
                        d.file_name,
                        kc.content,
                        kc.chunk_index,
                        kc.page_number,
                        kc.metadata,
                        1 - (kc.embedding <=> %s::vector) AS similarity
                    FROM knowledge_chunks kc
                    JOIN documents d
                        ON d.id = kc.document_id
                    WHERE kc.project_id = %s
                    ORDER BY kc.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        embedding,
                        project_id,
                        embedding,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

        return [
            {
                "document_id": str(row[0]),
                "project_id": row[1],
                "file_name": row[2],
                "content": row[3],
                "chunk_index": row[4],
                "page_number": row[5],
                "metadata": row[6],
                "similarity": float(row[7]),
            }
            for row in rows
        ]

    
    

    def search_keyword_chunks(
        self,
        query: str,
        project_id: str,
        limit: int = 5,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not project_id or not project_id.strip():
            raise ValueError("Project ID is required.")

        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50.")

        terms = re.findall(r"[a-zA-Z0-9]+", query.lower())

        stop_words = {
            "what", "are", "is", "the", "during",
            "a", "an", "of", "should", "does"
        }

        search_query = " | ".join(
            term for term in terms
            if term not in stop_words
        )

        if not search_query:
            return []

        with self._get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        kc.document_id,
                        kc.project_id,
                        d.file_name,
                        kc.content,
                        kc.chunk_index,
                        kc.page_number,
                        kc.metadata,
                        ts_rank_cd(
                            to_tsvector(
                                'simple',
                                replace(kc.content, '/', ' ')
                            ),
                            to_tsquery('simple', %s)
                        ) AS keyword_score
                    FROM knowledge_chunks kc
                    JOIN documents d
                        ON d.id = kc.document_id
                    WHERE kc.project_id = %s
                    AND to_tsvector(
                        'simple',
                        replace(kc.content, '/', ' ')
                    ) @@ to_tsquery('simple', %s)
                    ORDER BY keyword_score DESC
                    LIMIT %s
                    """,
                    (
                        search_query,
                        project_id,
                        search_query,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

        return [
            {
                "document_id": str(row[0]),
                "project_id": row[1],
                "file_name": row[2],
                "content": row[3],
                "chunk_index": row[4],
                "page_number": row[5],
                "metadata": row[6],
                "keyword_score": float(row[7]),
            }
            for row in rows
        ]


    def search_hybrid_chunks(
        self,
        query: str,
        query_embedding: list[float],
        project_id: str,
        limit: int = 5,
        candidate_limit: int = 20,
        rrf_k: int = 60,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not project_id:
            raise ValueError("Project ID is required.")

        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50.")

        if candidate_limit < limit or candidate_limit > 100:
            raise ValueError(
                "Candidate limit must be between limit and 100."
            )

        if rrf_k < 1:
            raise ValueError("RRF constant must be positive.")

        # Step 1: Run semantic search
        semantic_results = self.search_similar_chunks(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=candidate_limit,
        )

        # Step 2: Run keyword search
        keyword_results = self.search_keyword_chunks(
            query=query,
            project_id=project_id,
            limit=candidate_limit,
        )

        # Step 3: Merge results using document and chunk identity
        combined = {}

        for rank, result in enumerate(semantic_results, start=1):

            key = (
                result["document_id"],
                result["chunk_index"],
            )

            combined[key] = {
                **result,
                "semantic_rank": rank,
                "keyword_rank": None,
                "rrf_score": 1 / (rrf_k + rank),
            }

        for rank, result in enumerate(keyword_results, start=1):

            key = (
                result["document_id"],
                result["chunk_index"],
            )

            if key not in combined:
                combined[key] = {
                    **result,
                    "semantic_rank": None,
                    "keyword_rank": rank,
                    "rrf_score": 0.0,
                }

            else:
                combined[key]["keyword_rank"] = rank

            combined[key]["rrf_score"] += (
                1 / (rrf_k + rank)
            )
 
        for item in combined.values():
            print(
                f"Chunk: {item['chunk_index']}, "
                f"Semantic rank: {item['semantic_rank']}, "
                f"Keyword rank: {item['keyword_rank']}, "
                f"RRF score: {item['rrf_score']:.6f}"
            )
        # Step 4: Sort by combined RRF score
        ranked_results = sorted(
            combined.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        return ranked_results[:limit]


