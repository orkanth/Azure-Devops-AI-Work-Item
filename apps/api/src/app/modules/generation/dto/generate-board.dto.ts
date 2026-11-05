
import { IsNotEmpty, IsString, MaxLength, MinLength } from 'class-validator';

export class GenerateBoardDto {
  @IsString()
  @IsNotEmpty()
  @MinLength(10)
  @MaxLength(20000)
  requirement!: string;
}
