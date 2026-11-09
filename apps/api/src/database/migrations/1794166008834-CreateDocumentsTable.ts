import { MigrationInterface, QueryRunner } from "typeorm";

export class CreateDocumentsTable1794166008834 implements MigrationInterface {
    name = 'CreateDocumentsTable1794166008834'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`CREATE TABLE "documents" ("id" uuid NOT NULL DEFAULT gen_random_uuid(), "project_id" character varying(128) NOT NULL, "file_name" character varying(255) NOT NULL, "document_type" character varying(50) NOT NULL, "description" text, "storage_provider" character varying(30) NOT NULL, "storage_key" text NOT NULL, "content_type" character varying(150) NOT NULL, "size_bytes" integer NOT NULL, "checksum" character(64), "version" integer NOT NULL DEFAULT '1', "status" character varying(20) NOT NULL DEFAULT 'uploaded', "uploaded_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "indexed_at" TIMESTAMP WITH TIME ZONE, CONSTRAINT "PK_ac51aa5181ee2036f5ca482857c" PRIMARY KEY ("id"))`);
        await queryRunner.query(`CREATE INDEX "IDX_documents_checksum" ON "documents" ("project_id", "checksum") `);
        await queryRunner.query(`CREATE INDEX "IDX_documents_project_id" ON "documents" ("project_id") `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`DROP INDEX "public"."IDX_documents_project_id"`);
        await queryRunner.query(`DROP INDEX "public"."IDX_documents_checksum"`);
        await queryRunner.query(`DROP TABLE "documents"`);
    }

}
