import { Controller, Get } from '@nestjs/common';
import {
  WorkItemsService,
  WorkItemResponse,
} from './work-items.service';

@Controller('work-items')
export class WorkItemsController {
  constructor(
    private readonly workItemsService: WorkItemsService,
  ) {}

  @Get()
  findAll(): Promise<WorkItemResponse[]> {
    return this.workItemsService.findAll();
  }
}