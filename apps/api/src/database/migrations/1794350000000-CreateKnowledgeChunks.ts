
import { MigrationInterface, QueryRunner } from 'typeorm';

export class CreateKnowledgeChunks1794350000000
  implements MigrationInterface
{
  name = 'CreateKnowledgeChunks1794350000000';

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      CREATE TABLE knowledge_chunks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        document_id UUID NOT NULL,
        project_id VARCHAR(128) NOT NULL,

        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        page_number INTEGER,

        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

        embedding VECTOR(1536) NOT NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT fk_knowledge_chunks_document
          FOREIGN KEY (document_id)
          REFERENCES documents(id)
          ON DELETE CASCADE,

        CONSTRAINT uq_knowledge_chunks_document_index
          UNIQUE (document_id, chunk_index)
      );
    `);

    await queryRunner.query(`
      CREATE INDEX idx_knowledge_chunks_project_id
      ON knowledge_chunks (project_id);
    `);

    await queryRunner.query(`
      CREATE INDEX idx_knowledge_chunks_document_id
      ON knowledge_chunks (document_id);
    `);

    await queryRunner.query(`
      CREATE INDEX idx_knowledge_chunks_embedding
      ON knowledge_chunks
      USING hnsw (embedding vector_cosine_ops);
    `);

    await queryRunner.query(`
      CREATE INDEX idx_knowledge_chunks_content_search
      ON knowledge_chunks
      USING GIN (to_tsvector('simple', content));
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      DROP TABLE IF EXISTS knowledge_chunks;
    `);
  }
}
