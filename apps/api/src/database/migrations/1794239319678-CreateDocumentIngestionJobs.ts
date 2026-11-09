import { MigrationInterface, QueryRunner } from "typeorm";

export class CreateDocumentIngestionJobs1794239319678 implements MigrationInterface {
    name = 'CreateDocumentIngestionJobs1794239319678'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`CREATE TABLE "document_ingestion_jobs" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "document_id" uuid NOT NULL, "status" character varying(20) NOT NULL DEFAULT 'queued', "attempt_count" integer NOT NULL DEFAULT '0', "max_attempts" integer NOT NULL DEFAULT '3', "error_message" text, "started_at" TIMESTAMP WITH TIME ZONE, "completed_at" TIMESTAMP WITH TIME ZONE, "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), CONSTRAINT "PK_1ab2f5af0c0743626b9320cbadb" PRIMARY KEY ("id"))`);
        await queryRunner.query(`CREATE INDEX "IDX_ingestion_jobs_status" ON "document_ingestion_jobs" ("status") `);
        await queryRunner.query(`CREATE INDEX "IDX_ingestion_jobs_document_id" ON "document_ingestion_jobs" ("document_id") `);
        await queryRunner.query(`ALTER TABLE "document_ingestion_jobs" ADD CONSTRAINT "FK_0c00770f00f8a7ff0543f21eb78" FOREIGN KEY ("document_id") REFERENCES "documents"("id") ON DELETE CASCADE ON UPDATE NO ACTION`);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`ALTER TABLE "document_ingestion_jobs" DROP CONSTRAINT "FK_0c00770f00f8a7ff0543f21eb78"`);
        await queryRunner.query(`DROP INDEX "public"."IDX_ingestion_jobs_document_id"`);
        await queryRunner.query(`DROP INDEX "public"."IDX_ingestion_jobs_status"`);
        await queryRunner.query(`DROP TABLE "document_ingestion_jobs"`);
    }

}
