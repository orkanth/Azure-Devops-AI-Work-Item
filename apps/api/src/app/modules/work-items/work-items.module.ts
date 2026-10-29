import { Module } from '@nestjs/common'; 
import { WorkItemsController } from './work-items.controller';
import { WorkItemsService } from './work-items.service';
import { AzureDevOpsModule } from '../azure-devops/azure-devops.module';

@Module({
  imports: [AzureDevOpsModule],
  controllers: [WorkItemsController],
  providers: [WorkItemsService],
})
export class WorkItemsModule {}