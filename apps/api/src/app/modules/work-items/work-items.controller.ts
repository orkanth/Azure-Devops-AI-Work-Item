import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Post,
} from '@nestjs/common';

import { CreateWorkItemDto } from './dto/create-work-item.dto';
import { UpdateWorkItemDto } from './dto/update-work-item.dto';
import { AssignWorkItemDto } from './dto/assign-work-item.dto';
import { DeleteWorkItemDto } from './dto/delete-work-item.dto';
import { WorkItemsService } from './work-items.service';

@Controller('work-items')
export class WorkItemsController {
  constructor(private readonly workItemsService: WorkItemsService) {}

  @Get()
  findAll() {
    return this.workItemsService.findAll();
  }

  @Post()
  create(@Body() dto: CreateWorkItemDto) {
    return this.workItemsService.create(dto);
  }

  @Patch(':id')
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateWorkItemDto,
  ) {
    return this.workItemsService.update(id, dto);
  }

  @Patch(':id/assignment')
  assign(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: AssignWorkItemDto,
  ) {
    return this.workItemsService.assign(id, dto.assignedTo);
  }
  @Delete(':id')
  delete(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: DeleteWorkItemDto,
  ) {
    return this.workItemsService.delete(id, dto);
  }
}
