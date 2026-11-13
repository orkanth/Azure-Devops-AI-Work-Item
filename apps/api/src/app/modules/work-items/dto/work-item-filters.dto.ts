import { Type } from 'class-transformer';
import { IsIn, IsInt, IsOptional, IsString, MaxLength } from 'class-validator';

export class WorkItemFiltersDto {
  @IsOptional()
  @IsString()
  @MaxLength(200)
  type?: string;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  state?: string;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  assignedTo?: string;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @IsIn([1, 2, 3, 4])
  priority?: number;
}