
import { Controller, Get, Query } from '@nestjs/common'; 
import { AzureDevOpsService } from '../azure-devops/azure-devops.service';

@Controller('users')
export class UsersController {
  constructor(
    private readonly azureDevOpsService: AzureDevOpsService,
  ) {}

  @Get('search')
  searchUsers(@Query('name') name: string) {
    return this.azureDevOpsService.searchUsers(name);
  }
}
