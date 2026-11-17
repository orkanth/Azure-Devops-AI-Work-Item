
from uuid import UUID
import re
import psycopg
import math
from psycopg.types.json import Jsonb

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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
        Replace all indexed chunks for a document atomically.
        """

        if not chunks:
            raise ValueError("Cannot save an empty chunk list.")

        first_chunk = chunks[0]

        try:
            document_id = UUID(str(first_chunk["document_id"]))
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Invalid or missing document ID.") from exc

        project_id = first_chunk.get("project_id")

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Project ID is required.")

        validated_chunks = []

        for chunk in chunks:
            try:
                chunk_document_id = UUID(str(chunk["document_id"]))
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError("Invalid chunk document ID.") from exc

            if chunk_document_id != document_id:
                raise ValueError("Chunks contain different document IDs.")

            if chunk.get("project_id") != project_id:
                raise ValueError("Chunks contain different project IDs.")

            content = chunk.get("content")
            if not isinstance(content, str):
                raise ValueError("Chunk content must be a string.")

            embedding = chunk.get("embedding")

            if not isinstance(embedding, (list, tuple)):
                raise ValueError("Chunk embedding must be a list.")

            if len(embedding) != self.EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Expected {self.EMBEDDING_DIMENSIONS} embedding "
                    f"dimensions, got {len(embedding)}."
                )

            try:
                embedding_values = [float(value) for value in embedding]
            except (ValueError, TypeError) as exc:
                raise ValueError("Embedding contains invalid values.") from exc

            if not all(
                math.isfinite(value)
                for value in embedding_values
            ):
                raise ValueError("Embedding contains non-finite values.")

            chunk_index = chunk.get("chunk_index")

            if (
                not isinstance(chunk_index, int)
                or isinstance(chunk_index, bool)
                or chunk_index < 0
            ):
                raise ValueError("Chunk index must be a non-negative integer.")

            metadata = chunk.get("metadata") or {}

            if not isinstance(metadata, dict):
                raise ValueError("Chunk metadata must be a dictionary.")

            page_number = chunk.get("page_number")

            validated_chunks.append({
                "content": content,
                "chunk_index": chunk_index,
                "page_number": page_number,
                "metadata": metadata,
                "embedding": embedding_values,
            })

        # Prevent duplicate chunk indexes within the incoming batch.
        indexes = [chunk["chunk_index"] for chunk in validated_chunks]

        if len(indexes) != len(set(indexes)):
            raise ValueError("Duplicate chunk indexes found.")

        # The connection context commits on success and rolls back on error.
        with self._get_connection() as connection:
            with connection.cursor() as cursor:

                # Verify document existence and project ownership.
                cursor.execute(
                    """
                    SELECT project_id
                    FROM documents
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (str(document_id),),
                )

                document = cursor.fetchone()

                if document is None:
                    raise ValueError("Document does not exist.")

                if document[0] != project_id:
                    raise ValueError(
                        "Document project ID does not match chunk project ID."
                    )

                # Remove old chunks inside the same transaction.
                cursor.execute(
                    """
                    DELETE FROM knowledge_chunks
                    WHERE document_id = %s
                    """,
                    (str(document_id),),
                )

                # Insert replacement chunks.
                cursor.executemany(
                    """
                    INSERT INTO knowledge_chunks (
                        document_id,
                        project_id,
                        content,
                        chunk_index,
                        page_number,
                        metadata,
                        embedding
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s::vector
                    )
                    """,
                    [
                        (
                            str(document_id),
                            project_id,
                            chunk["content"],
                            chunk["chunk_index"],
                            chunk["page_number"],
                            Jsonb(chunk["metadata"]),
                            "[" + ",".join(
                                str(value)
                                for value in chunk["embedding"]
                            ) + "]",
                        )
                        for chunk in validated_chunks
                    ],
                )

        return len(validated_chunks)

    
    
    
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

        if not isinstance(project_id, str) or not project_id.strip():
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
            logger.debug(
                "Chunk: %s | Semantic rank: %s | "
                "Keyword rank: %s | RRF score: %.6f",
                item["chunk_index"],
                item["semantic_rank"],
                item["keyword_rank"],
                item["rrf_score"],
            )
        # Step 4: Sort by combined RRF score
        ranked_results = sorted(
            combined.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        return ranked_results[:limit]


