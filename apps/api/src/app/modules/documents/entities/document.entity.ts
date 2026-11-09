import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

export enum DocumentStatus {
  UPLOADED = 'uploaded',
  PENDING = 'pending',
  PROCESSING = 'processing',
  INDEXED = 'indexed',
  FAILED = 'failed',
  DELETING = 'deleting',
  DELETED = 'deleted',
}

@Entity('documents')
@Index('IDX_documents_project_id', ['projectId'])
@Index('UQ_documents_project_checksum', ['projectId', 'checksum'], {
  unique: true,
  where: '"checksum" IS NOT NULL',
})
export class DocumentEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'project_id', type: 'varchar', length: 128 })
  projectId!: string;

  @Column({ name: 'file_name', type: 'varchar', length: 255 })
  fileName!: string;

  @Column({ name: 'document_type', type: 'varchar', length: 50 })
  documentType!: string;

  @Column({ type: 'text', nullable: true })
  description?: string | null;

  @Column({ name: 'storage_provider', type: 'varchar', length: 30 })
  storageProvider!: string;

  @Column({ name: 'storage_key', type: 'text' })
  storageKey!: string;

  @Column({ name: 'content_type', type: 'varchar', length: 150 })
  contentType!: string;

  @Column({ name: 'size_bytes', type: 'integer' })
  sizeBytes!: number;

  @Column({ type: 'char', length: 64, nullable: true })
  checksum?: string | null;

  @Column({ type: 'integer', default: 1 })
  version!: number;

  @Column({
    type: 'varchar',
    length: 20,
    default: DocumentStatus.UPLOADED,
  })
  status!: DocumentStatus;

  @CreateDateColumn({ name: 'uploaded_at', type: 'timestamptz' })
  uploadedAt!: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt!: Date;

  @Column({ name: 'indexed_at', type: 'timestamptz', nullable: true })
  indexedAt?: Date | null;
}
