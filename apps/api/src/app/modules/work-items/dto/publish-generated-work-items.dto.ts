
import {
  ArrayMinSize,
  IsArray,
  IsIn,
  IsOptional,
  IsString,
  MaxLength,
  MinLength,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';
import { IsUUID } from 'class-validator';
export type GeneratedWorkItemType =
  | 'Epic'
  | 'Feature'
  | 'User Story'
  | 'Task'
  | 'Bug';

export class GeneratedWorkItemDto {
  @IsIn(['Epic', 'Feature', 'User Story', 'Task', 'Bug'])
  type!: GeneratedWorkItemType;

  @IsString()
  @MinLength(3)
  @MaxLength(255)
  title!: string;

  @IsOptional()
  @IsString()
  @MaxLength(20000)
  description?: string;

  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  acceptance_criteria?: string[];

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => GeneratedWorkItemDto)
  children?: GeneratedWorkItemDto[];
}

export class PublishGeneratedWorkItemsDto {
  @IsIn(['Epic', 'Feature', 'User Story', 'Task', 'Bug'])
  requested_type!: GeneratedWorkItemType;

  @IsArray()
  @ArrayMinSize(1)
  @ValidateNested({ each: true })
  @Type(() => GeneratedWorkItemDto)
  items!: GeneratedWorkItemDto[];

  @IsOptional()
  @IsString()
  @MaxLength(255)
  parent_reference?: string | null;

  @IsUUID()
  publishId!: string;
}
