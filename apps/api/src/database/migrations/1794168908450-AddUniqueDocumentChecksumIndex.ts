import { MigrationInterface, QueryRunner } from "typeorm";

export class AddUniqueDocumentChecksumIndex1794168908450 implements MigrationInterface {
    name = 'AddUniqueDocumentChecksumIndex1794168908450'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`DROP INDEX "public"."IDX_documents_checksum"`);
        await queryRunner.query(`CREATE UNIQUE INDEX "UQ_documents_project_checksum" ON "documents" ("project_id", "checksum") WHERE "checksum" IS NOT NULL`);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`DROP INDEX "public"."UQ_documents_project_checksum"`);
        await queryRunner.query(`CREATE INDEX "IDX_documents_checksum" ON "documents"  ("project_id", "checksum") `);
    }

}
