
import {
  IsEnum,
  IsNotEmpty,
  IsOptional,
  IsString,
  MaxLength,
} from 'class-validator';

export enum DocumentType {
  TTD = 'TTD',
  API_SPECIFICATION = 'API_SPECIFICATION',
  TECHNICAL_DESIGN = 'TECHNICAL_DESIGN',
  REQUIREMENTS = 'REQUIREMENTS',
  GENERAL = 'GENERAL',
}

export class CreateDocumentDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(128)
  projectId!: string;

  @IsEnum(DocumentType)
  documentType!: DocumentType;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;
}
