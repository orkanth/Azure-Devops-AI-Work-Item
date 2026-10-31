import {
  IsIn,
  IsInt,
  IsOptional,
  IsString,
  MaxLength,
  Min,
  MinLength,
} from 'class-validator';

export class CreateWorkItemDto {
  @IsIn(['Epic', 'Feature', 'User Story', 'Task', 'Bug'])
  type!: 'Epic' | 'Feature' | 'User Story' | 'Task' | 'Bug';

  @IsString()
  @MinLength(1)
  @MaxLength(255)
  title!: string;

  @IsOptional()
  @IsString()
  @MaxLength(20000)
  description?: string;

  @IsOptional()
  @IsString()
  @MaxLength(256)
  assignedTo?: string;

  @IsOptional()
  @IsIn(['Low', 'Medium', 'High'])
  priority?: 'Low' | 'Medium' | 'High';

  @IsOptional()
  @IsInt()
  @Min(1)
  parentId?: number;
}