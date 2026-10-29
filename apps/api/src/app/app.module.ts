import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { HealthModule } from './modules/health/health.module';
import { WorkItemsModule } from './modules/work-items/work-items.module';

@Module({
  imports: [HealthModule, WorkItemsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
