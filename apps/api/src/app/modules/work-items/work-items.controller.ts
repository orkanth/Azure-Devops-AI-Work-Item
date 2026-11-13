import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';

import { CreateWorkItemDto } from './dto/create-work-item.dto';
import { UpdateWorkItemDto } from './dto/update-work-item.dto';
import { AssignWorkItemDto } from './dto/assign-work-item.dto';
import { DeleteWorkItemDto } from './dto/delete-work-item.dto';
import { WorkItemsService } from './work-items.service';
import { PublishEpicDto } from './dto/publish-work-items.dto'; 
import { WorkItemFiltersDto } from './dto/work-item-filters.dto';

@Controller('work-items')
export class WorkItemsController {
  constructor(private readonly workItemsService: WorkItemsService) {}
 
  @Get()
  findAll(@Query() filters: WorkItemFiltersDto) {
    return this.workItemsService.findAll(filters);
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
  @Post('publish')
  publish(@Body() dto: PublishEpicDto) {
    return this.workItemsService.publish(dto);
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.workItemsService.findOne(Number(id));
  }
}
