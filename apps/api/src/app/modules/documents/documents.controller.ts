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
  Header,
  StreamableFile,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';

import { FileInterceptor } from '@nestjs/platform-express';
import { CreateDocumentDto } from './dto/create-document.dto';
import { DocumentsService } from './documents.service';
import { FindIngestionJobsDto } from './dto/find-ingestion-jobs.dto';
import { AskDocumentQuestionDto } from './dto/ask-document-question.dto';

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
  @HttpCode(HttpStatus.OK)
  async claimNextIngestionJob() {
    const job = await this.documentsService.claimNextIngestionJob();
    return { job };
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

    return this.documentsService.failIngestionJob(jobId, errorMessage);
  }

  @Get(':documentId')
  findById(@Param('documentId', ParseUUIDPipe) documentId: string) {
    return this.documentsService.findById(documentId);
  }

  @Post('ask')
  askQuestion(@Body() dto: AskDocumentQuestionDto) {
    return this.documentsService.askQuestion(dto);
  }

  @Get(':documentId/content')
  @Header('Cache-Control', 'no-store')
  async getDocumentContent(
    @Param('documentId', ParseUUIDPipe) documentId: string,
  ) {
    const document = await this.documentsService.getDocumentContent(documentId);

    return new StreamableFile(document.content, {
      type: document.contentType,
      disposition: 'attachment',
    });
  }
}
