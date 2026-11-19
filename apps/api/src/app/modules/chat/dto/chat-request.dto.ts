
import { IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';

export class ChatRequestDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(10000)
  question?: string;

  @IsOptional()
  @IsString()
  @IsNotEmpty()
  conversation_id?: string;

  @IsOptional()
  @IsString()
  @IsNotEmpty()
  project_id?: string;
}
