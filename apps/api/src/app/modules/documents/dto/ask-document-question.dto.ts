import { IsInt, IsNotEmpty, IsString, Max, Min } from 'class-validator';

export class AskDocumentQuestionDto {
    @IsString()
    @IsNotEmpty()
    question!: string;

    @IsString()
    @IsNotEmpty()
    project_id!: string;
  
    @IsInt()
    @Min(1)
    @Max(50)
    limit = 5;
}