
import {
  ArrayNotEmpty,
  IsArray,
  IsNotEmpty,
  IsString,
  IsUUID,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';

export class PublishTaskDto {
  @IsString()
  @IsNotEmpty()
  title!: string;

  @IsString()
  description!: string;

  @IsArray()
  acceptance_criteria!: string[];
}

export class PublishUserStoryDto {
  @IsString()
  @IsNotEmpty()
  title!: string;

  @IsString()
  description!: string;

  @IsArray()
  acceptance_criteria!: string[];

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PublishTaskDto)
  tasks!: PublishTaskDto[];
}

export class PublishFeatureDto {
  @IsString()
  @IsNotEmpty()
  title!: string;

  @IsString()
  description!: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PublishUserStoryDto)
  user_stories!: PublishUserStoryDto[];
}

export class PublishEpicDto {
  @IsUUID()
  publishId!: string;

  @IsString()
  @IsNotEmpty()
  title!: string;

  @IsString()
  description!: string;

  @IsArray()
  @ArrayNotEmpty()
  @ValidateNested({ each: true })
  @Type(() => PublishFeatureDto)
  features!: PublishFeatureDto[];
}
