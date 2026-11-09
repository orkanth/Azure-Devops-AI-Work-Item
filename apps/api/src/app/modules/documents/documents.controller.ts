import {
  BadRequestException,
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
  UploadedFile,
  UseInterceptors,
  Query,
} from '@nestjs/common';

import { FileInterceptor } from '@nestjs/platform-express';
import { CreateDocumentDto } from './dto/create-document.dto';
import { DocumentsService } from './documents.service';
import { FindIngestionJobsDto } from './dto/find-ingestion-jobs.dto';

@Controller('documents')
export class DocumentsController {
  constructor(private readonly documentsService: DocumentsService) {}

  @Post()
  @UseInterceptors(
    FileInterceptor('file', {
      limits: {
        fileSize: 20 * 1024 * 1024,
      },
    }),
  )
  upload(
    @UploadedFile() file: Express.Multer.File,
    @Body() dto: CreateDocumentDto,
  ) {
    if (!file) {
      throw new BadRequestException('Document file is required.');
    }

    return this.documentsService.upload(file, dto);
  }

  @Get('ingestion-jobs')
  findIngestionJobs(@Query() dto: FindIngestionJobsDto) {
    return this.documentsService.findIngestionJobs(dto);
  }

  @Post('ingestion-jobs/claim')
  claimNextIngestionJob() {
    return this.documentsService.claimNextIngestionJob();
  }

  @Post('ingestion-jobs/:jobId/complete')
  completeIngestionJob(@Param('jobId', ParseUUIDPipe) jobId: string) {
    return this.documentsService.completeIngestionJob(jobId);
  }

@Post('ingestion-jobs/:jobId/fail')
failIngestionJob(
  @Param('jobId', ParseUUIDPipe) jobId: string,
  @Body('errorMessage') errorMessage: string,
) {
  console.log('Job ID:', jobId);
  console.log('Error message:', errorMessage);

  return this.documentsService.failIngestionJob(
    jobId,
    errorMessage,
  );
}

  @Get(':documentId')
  findById(@Param('documentId', ParseUUIDPipe) documentId: string) {
    return this.documentsService.findById(documentId);
  }
}
