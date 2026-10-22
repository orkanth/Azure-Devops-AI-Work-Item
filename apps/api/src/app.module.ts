import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HealthController } from './modules/health/health.controller';
import { resolve } from 'node:path';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true ,    envFilePath: resolve(process.cwd(), '.env'),})],
  controllers: [HealthController],
})
export class AppModule {}
