import { Injectable } from '@nestjs/common'; 
import { AzureDevOpsService, AzureDevOpsWorkItem } from '../azure-devops/azure-devops.service';

export interface WorkItemResponse {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedTo: string;
  priority: 'Low' | 'Medium' | 'High';
  updatedAt: string;
  parentId?: number;
  url: string;
}

@Injectable()
export class WorkItemsService {
  constructor(
    private readonly azureDevOpsService: AzureDevOpsService,
  ) {}

  async findAll(): Promise<WorkItemResponse[]> {
    const items = await this.azureDevOpsService.getWorkItems();

    return items.map((item) => this.mapWorkItem(item));
  }

  private mapWorkItem(item: AzureDevOpsWorkItem): WorkItemResponse {
    const fields = item.fields ?? {};
    const parentRelation = item.relations?.find(
      (relation) =>
        relation.rel === 'System.LinkTypes.Hierarchy-Reverse',
    );

    const parentMatch =
      parentRelation?.url.match(/\/workItems\/(\d+)\/?$/i);

    const assignedTo = fields['System.AssignedTo'];

    const assignee =
      typeof assignedTo === 'string'
        ? assignedTo
        : assignedTo &&
            typeof assignedTo === 'object' &&
            'displayName' in assignedTo &&
            typeof assignedTo.displayName === 'string'
          ? assignedTo.displayName
          : 'Unassigned';

    const rawPriority = Number(
      fields['Microsoft.VSTS.Common.Priority'],
    );

    const priority: WorkItemResponse['priority'] =
      rawPriority === 1 || rawPriority === 2
        ? 'High'
        : rawPriority === 4
          ? 'Low'
          : 'Medium';

    const organization =
      process.env.AZURE_DEVOPS_ORG ?? '';
    const project =
      process.env.AZURE_DEVOPS_PROJECT ?? '';

    return {
      id: item.id,
      title: this.getString(fields['System.Title'], `Item ${item.id}`),
      type: this.getString(fields['System.WorkItemType'], 'Task'),
      state: this.getString(fields['System.State'], 'New'),
      assignedTo: assignee || 'Unassigned',
      priority,
      updatedAt: this.getString(fields['System.ChangedDate'], ''),
      ...(parentMatch ? { parentId: Number(parentMatch[1]) } : {}),
      url:
        `https://dev.azure.com/${encodeURIComponent(organization)}` +
        `/${encodeURIComponent(project)}/_workitems/edit/${item.id}`,
    };
  }

  private getString(value: unknown, fallback: string): string {
    return typeof value === 'string' && value.length > 0
      ? value
      : fallback;
  }
}