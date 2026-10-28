import { Injectable } from '@nestjs/common';

@Injectable()
export class HealthService {
  getHealth() {
    return {
      status: 'ok',
      service: 'azure-devops-ai-work-item-generator-api',
      timestamp: new Date().toISOString(),
    };
  }
}