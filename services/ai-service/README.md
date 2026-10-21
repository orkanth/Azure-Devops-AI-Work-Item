# Python AI Service

Planned responsibilities: document extraction, chunking, embedding/retrieval, LLM orchestration, structured work-item generation and hierarchy validation.

Suggested flow:
1. Parse prompt and optional document reference.
2. Retrieve relevant chunks from ChromaDB when document context is needed.
3. Ask the LLM for schema-constrained output.
4. Validate required fields and parent-child references.
5. Check for possible duplicates through approved tools.
6. Return a proposal for human review.
7. Publish only after the API confirms explicit approval.

Keep prompts, schemas and graph nodes separate so they can be tested independently.
