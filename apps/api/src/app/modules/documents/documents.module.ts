
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { DocumentsController } from './documents.controller';
import { DocumentsService } from './documents.service';
import { DocumentEntity } from './entities/document.entity';
import { LocalDocumentStorageService } from './storage/local-document-storage.service';
import { DOCUMENT_STORAGE_PROVIDER } from './storage/document-storage.provider';
import { DocumentIngestionJobEntity } from './entities/document-ingestion-job.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([DocumentEntity, DocumentIngestionJobEntity]),
  ],
  controllers: [DocumentsController],
  providers: [
    DocumentsService,
    {
      provide: DOCUMENT_STORAGE_PROVIDER,
      useClass: LocalDocumentStorageService,
    },
  ],
    exports: [
    DocumentsService,
  ],
})
export class DocumentsModule {}
