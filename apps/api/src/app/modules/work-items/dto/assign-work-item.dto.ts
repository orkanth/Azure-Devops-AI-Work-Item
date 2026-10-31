import {
  IsEmail,
  IsNotEmpty,
  IsString,
} from 'class-validator';

export class AssignWorkItemDto {
  @IsString()
  @IsNotEmpty()
  @IsEmail()
  assignedTo!: string;
}