import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AzureDevOpsService } from './azure-devops.service';

@Module({
  imports: [ConfigModule],
  providers: [AzureDevOpsService],
  exports: [AzureDevOpsService],
})
export class AzureDevOpsModule {}