import {
  IsEnum,
  IsInt,
  IsOptional,
  Max,
  Min,
} from 'class-validator';

import { Type } from 'class-transformer';

import { IngestionJobStatus } from '../entities/document-ingestion-job.entity';

export class FindIngestionJobsDto {
  @IsOptional()
  @IsEnum(IngestionJobStatus)
  status?: IngestionJobStatus;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page = 1;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  pageSize = 20;
}