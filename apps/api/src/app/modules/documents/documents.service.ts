import {
  BadGatewayException,
  BadRequestException,
  ConflictException,
  Inject,
  Injectable,
  InternalServerErrorException,
  Logger,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { createHash, randomUUID } from 'node:crypto';
import { EntityManager, Repository, DataSource } from 'typeorm';

import { CreateDocumentDto } from './dto/create-document.dto';
import {
  DOCUMENT_STORAGE_PROVIDER,
  DocumentStorageProvider,
} from './storage/document-storage.provider';
import { DocumentEntity, DocumentStatus } from './entities/document.entity';
import {
  DocumentIngestionJobEntity,
  IngestionJobStatus,
} from './entities/document-ingestion-job.entity';
import { FindIngestionJobsDto } from './dto/find-ingestion-jobs.dto';
import { AskDocumentQuestionDto } from './dto/ask-document-question.dto';
import { ConfigService } from '@nestjs/config';

export interface DocumentSource {
  source: number;
  file_name: string;
  document_id: string;
  page_number: number | null;
  chunk_index: number;
  semantic_rank?: number | null;
  keyword_rank?: number | null;
  rrf_score?: number | null;
}

export interface AskDocumentQuestionResponse {
  answer: string;
  sources: DocumentSource[];
}

interface AiServiceResponse {
  status: string;
  data: AskDocumentQuestionResponse;
}
@Injectable()
export class DocumentsService {
  private readonly logger = new Logger(DocumentsService.name);

  constructor(
    @Inject(DOCUMENT_STORAGE_PROVIDER)
    private readonly storageProvider: DocumentStorageProvider,

    @InjectRepository(DocumentEntity)
    private readonly documentsRepository: Repository<DocumentEntity>,

    @InjectRepository(DocumentIngestionJobEntity)
    private readonly ingestionJobsRepository: Repository<DocumentIngestionJobEntity>,

    private readonly dataSource: DataSource,
    private readonly configService: ConfigService,
  ) {}

  async upload(file: Express.Multer.File, dto: CreateDocumentDto) {
    if (!file?.buffer) {
      throw new BadRequestException('Document file is required.');
    }

    // 1. Calculate the SHA-256 checksum.
    const checksum = createHash('sha256').update(file.buffer).digest('hex');

    // 2. Check for an existing document before saving the file.
    const existingDocument = await this.documentsRepository.findOne({
      where: {
        projectId: dto.projectId,
        checksum,
      },
    });

    if (existingDocument) {
      return this.toUploadResponse(existingDocument, true);
    }

    // 3. Save the physical document.
    const documentId = randomUUID();

    const storedDocument = await this.storageProvider.save(documentId, file);

    // 4. Prepare database metadata.
    const document = this.documentsRepository.create({
      id: documentId,
      projectId: dto.projectId,
      fileName: storedDocument.fileName,
      documentType: dto.documentType,
      description: dto.description ?? null,
      storageProvider: storedDocument.storageProvider,
      storageKey: storedDocument.storageKey,
      contentType: storedDocument.contentType,
      sizeBytes: storedDocument.sizeBytes,
      checksum,
      version: 1,
      status: DocumentStatus.UPLOADED,
    });

    try {
      const result = await this.dataSource.transaction(async (manager) => {
        const documentsRepository = manager.getRepository(DocumentEntity);

        const savedDocument = await documentsRepository.save(document);

        const ingestionJob = await this.createIngestionJob(
          savedDocument.id,
          manager,
        );

        return {
          savedDocument,
          ingestionJob,
        };
      });

      return {
        ...this.toUploadResponse(result.savedDocument),
        ingestionJob: {
          id: result.ingestionJob.id,
          status: result.ingestionJob.status,
        },
      };
    } catch (error) {
      // Clean up the physical file because metadata persistence failed.
      try {
        await this.storageProvider.delete(storedDocument.storageKey);
      } catch (cleanupError) {
        this.logger.error(
          `Could not clean up stored document ${documentId}`,
          cleanupError instanceof Error
            ? cleanupError.stack
            : String(cleanupError),
        );
      }

      // PostgreSQL error 23505 means a unique constraint was violated.
      const databaseError = error as {
        code?: string;
        constraint?: string;
        driverError?: {
          code?: string;
          constraint?: string;
        };
      };

      const errorCode = databaseError.driverError?.code ?? databaseError.code;

      const constraint =
        databaseError.driverError?.constraint ?? databaseError.constraint;

      if (
        errorCode === '23505' &&
        constraint === 'UQ_documents_project_checksum'
      ) {
        const existingDocument = await this.documentsRepository.findOne({
          where: {
            projectId: dto.projectId,
            checksum,
          },
        });

        if (existingDocument) {
          this.logger.log(
            `Duplicate upload detected for document ${existingDocument.id}`,
          );

          return this.toUploadResponse(existingDocument, true);
        }
      }

      this.logger.error(
        `Could not save document metadata for ${documentId}`,
        error instanceof Error ? error.stack : String(error),
      );

      throw new InternalServerErrorException(
        'Document metadata could not be saved.',
      );
    }
  }

  private toUploadResponse(document: DocumentEntity, duplicate = false) {
    return {
      documentId: document.id,
      fileName: document.fileName,
      fileSize: document.sizeBytes,
      projectId: document.projectId,
      documentType: document.documentType,
      description: document.description,
      storageProvider: document.storageProvider,
      storageKey: document.storageKey,
      checksum: document.checksum,
      status: document.status,
      uploadedAt: document.uploadedAt,
      duplicate,
      ...(duplicate
        ? { message: 'This document has already been uploaded.' }
        : {}),
    };
  }

  async findById(documentId: string) {
    const document = await this.documentsRepository.findOne({
      where: {
        id: documentId,
      },
    });

    if (!document) {
      throw new NotFoundException(
        `Document with ID ${documentId} was not found.`,
      );
    }

    return {
      documentId: document.id,
      fileName: document.fileName,
      projectId: document.projectId,
      documentType: document.documentType,
      description: document.description,
      contentType: document.contentType,
      fileSize: document.sizeBytes,
      checksum: document.checksum,
      status: document.status,
      uploadedAt: document.uploadedAt,
      indexedAt: document.indexedAt,
    };
  }

  async findQueuedIngestionJobs() {
    return this.ingestionJobsRepository.find({
      where: {
        status: IngestionJobStatus.QUEUED,
      },
      relations: {
        document: true,
      },
      order: {
        createdAt: 'ASC',
      },
    });
  }
  private async createIngestionJob(
    documentId: string,
    manager: EntityManager,
  ): Promise<DocumentIngestionJobEntity> {
    const repository = manager.getRepository(DocumentIngestionJobEntity);

    const job = repository.create({
      documentId,
      status: IngestionJobStatus.QUEUED,
      attemptCount: 0,
      maxAttempts: 3,
    });

    return repository.save(job);
  }

  async findIngestionJobs(dto: FindIngestionJobsDto) {
    const page = dto.page ?? 1;
    const pageSize = dto.pageSize ?? 20;

    const [jobs, total] = await this.ingestionJobsRepository.findAndCount({
      where: dto.status ? { status: dto.status } : {},
      relations: {
        document: true,
      },
      order: {
        createdAt: 'DESC',
      },
      skip: (page - 1) * pageSize,
      take: pageSize,
    });

    return {
      items: jobs,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    };
  }

  async claimNextIngestionJob(): Promise<DocumentIngestionJobEntity | null> {
    return this.dataSource.transaction(async (manager) => {
      const jobsRepository = manager.getRepository(DocumentIngestionJobEntity);

      // 1. Find and lock the oldest available job.
      const job = await jobsRepository
        .createQueryBuilder('job')
        .where('job.status = :status', {
          status: IngestionJobStatus.QUEUED,
        })
        .andWhere('job.attemptCount < job.maxAttempts')
        .orderBy('job.createdAt', 'ASC')
        .setLock('pessimistic_write')
        .setOnLocked('skip_locked')
        .getOne();

      // 2. No available job.
      if (!job) {
        return null;
      }

      // 3. Mark the job as processing.
      job.status = IngestionJobStatus.PROCESSING;
      job.attemptCount += 1;
      job.startedAt = new Date();
      job.errorMessage = null;

      await jobsRepository.save(job);

      // 4. Return the job with its document details.
      return jobsRepository.findOne({
        where: { id: job.id },
        relations: {
          document: true,
        },
      });
    });
  }

  async completeIngestionJob(
    jobId: string,
  ): Promise<DocumentIngestionJobEntity> {
    return this.dataSource.transaction(async (manager) => {
      const jobsRepository = manager.getRepository(DocumentIngestionJobEntity);

      const documentsRepository = manager.getRepository(DocumentEntity);

      // 1. Find and lock the ingestion job.
      const job = await jobsRepository.findOne({
        where: { id: jobId },
        lock: { mode: 'pessimistic_write' },
      });

      if (!job) {
        throw new NotFoundException(`Ingestion job ${jobId} not found`);
      }

      // 2. Only processing jobs can be completed.
      if (job.status !== IngestionJobStatus.PROCESSING) {
        throw new ConflictException(
          `Cannot complete job with status: ${job.status}`,
        );
      }

      // 3. Mark the ingestion job as completed.
      job.status = IngestionJobStatus.COMPLETED;
      job.completedAt = new Date();
      job.errorMessage = null;

      await jobsRepository.save(job);

      // 4. Update the associated document.
      await documentsRepository.update(
        { id: job.documentId },
        {
          status: DocumentStatus.INDEXED,
          indexedAt: new Date(),
        },
      );

      // 5. Return the completed job with document details.
      return jobsRepository.findOne({
        where: { id: job.id },
        relations: { document: true },
      }) as Promise<DocumentIngestionJobEntity>;
    });
  }

  async failIngestionJob(
    jobId: string,
    errorMessage: string,
  ): Promise<DocumentIngestionJobEntity> {
    return this.dataSource.transaction(async (manager) => {
      const jobsRepository = manager.getRepository(DocumentIngestionJobEntity);

      const documentsRepository = manager.getRepository(DocumentEntity);

      // 1. Find and lock the job.
      const job = await jobsRepository.findOne({
        where: { id: jobId },
        lock: { mode: 'pessimistic_write' },
      });

      if (!job) {
        throw new NotFoundException(`Ingestion job ${jobId} not found`);
      }

      // 2. Only processing jobs can fail.
      if (job.status !== IngestionJobStatus.PROCESSING) {
        throw new ConflictException(
          `Cannot fail job with status: ${job.status}`,
        );
      }

      // 3. Store the error.
      job.errorMessage = errorMessage;
      console.log('Before save:', job.errorMessage);
      // 4. Decide whether to retry or permanently fail.
      const canRetry = job.attemptCount < job.maxAttempts;

      job.status = canRetry
        ? IngestionJobStatus.QUEUED
        : IngestionJobStatus.FAILED;

      if (!canRetry) {
        job.completedAt = new Date();
      }

      await jobsRepository.save(job);
      console.log('After save:', job.errorMessage);
      // 5. Update the associated document.
      // 5. Update the associated document.
      await documentsRepository.update(
        { id: job.documentId },
        {
          status: canRetry ? DocumentStatus.PENDING : DocumentStatus.FAILED,
          indexedAt: null,
        },
      );

      // 6. Return the updated job.
      const updatedJob = await jobsRepository.findOne({
        where: { id: job.id },
        relations: { document: true },
      });

      console.log('After reload:', updatedJob?.errorMessage);

      return updatedJob as DocumentIngestionJobEntity;
    });
  }

  async askQuestion(
    dto: AskDocumentQuestionDto,
  ): Promise<AskDocumentQuestionResponse> {
    const aiServiceUrl = this.configService
      .get<string>('AI_SERVICE_URL', 'http://localhost:8000')
      .replace(/\/+$/, '');

    try {
      const response = await fetch(`${aiServiceUrl}/api/v1/documents/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: dto.question,
          project_id: dto.project_id,
          limit: dto.limit,
        }),
        signal: AbortSignal.timeout(120000),
      });

      if (!response.ok) {
        const errorBody = await response.text();

        this.logger.error(
          `AI document service returned HTTP ${response.status}: ${errorBody}`,
        );

        throw new BadGatewayException(
          'Document question-answering service could not process the request.',
        );
      }

      const result = (await response.json()) as AiServiceResponse;

      return result.data;
    } catch (error: unknown) {
      if (error instanceof BadGatewayException) {
        throw error;
      }

      if (error instanceof Error && error.name === 'TimeoutError') {
        this.logger.error('Document question-answering request timed out.');

        throw new ServiceUnavailableException(
          'Document question-answering took too long. Please try again.',
        );
      }

      this.logger.error(
        'Could not connect to document question-answering service.',
        error instanceof Error ? error.stack : undefined,
      );

      throw new ServiceUnavailableException(
        'Document question-answering service is currently unavailable.',
      );
    }
  }
}
