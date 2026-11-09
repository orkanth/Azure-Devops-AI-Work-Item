import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

import { DocumentEntity } from './document.entity';

export enum IngestionJobStatus {
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

@Entity('document_ingestion_jobs')
@Index('IDX_ingestion_jobs_document_id', ['documentId'])
@Index('IDX_ingestion_jobs_status', ['status'])
export class DocumentIngestionJobEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'document_id', type: 'uuid' })
  documentId!: string;

  @ManyToOne(() => DocumentEntity, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'document_id' })
  document!: DocumentEntity;

  @Column({
    type: 'varchar',
    length: 20,
    default: IngestionJobStatus.QUEUED,
  })
  status!: IngestionJobStatus;

  @Column({ name: 'attempt_count', default: 0 })
  attemptCount!: number;

  @Column({ name: 'max_attempts', default: 3 })
  maxAttempts!: number;

  @Column({
    name: 'error_message',
    type: 'text',
    nullable: true,
  })
  errorMessage!: string | null;

  @Column({
    name: 'started_at',
    type: 'timestamptz',
    nullable: true,
  })
  startedAt!: Date | null;

  @Column({
    name: 'completed_at',
    type: 'timestamptz',
    nullable: true,
  })
  completedAt!: Date | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt!: Date;
}
