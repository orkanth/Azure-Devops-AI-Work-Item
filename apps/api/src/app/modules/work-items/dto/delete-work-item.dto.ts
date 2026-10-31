import { Equals, IsBoolean } from 'class-validator';

export class DeleteWorkItemDto {
  @IsBoolean()
  @Equals(true)
  confirm!: boolean;
}