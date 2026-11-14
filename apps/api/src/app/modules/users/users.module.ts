
import { Module } from '@nestjs/common';
 
import { UsersController } from './users.controller';
import { AzureDevOpsModule } from '../azure-devops/azure-devops.module';

@Module({
  imports: [AzureDevOpsModule],
  controllers: [UsersController],
})
export class UsersModule {}
