import { BadRequestException, Injectable } from '@nestjs/common';
import {
  AzureDevOpsService,
  AzureDevOpsWorkItem,
} from '../azure-devops/azure-devops.service';
import { CreateWorkItemDto } from './dto/create-work-item.dto';
import { UpdateWorkItemDto } from './dto/update-work-item.dto';
import { DeleteWorkItemDto } from './dto/delete-work-item.dto';

export interface WorkItemResponse {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedToEmail?: string;
  assignedTo: string;
  priority: 'Low' | 'Medium' | 'High';
  updatedAt: string;
  parentId?: number;
  url: string;
}

@Injectable()
export class WorkItemsService {
  constructor(private readonly azureDevOpsService: AzureDevOpsService) {}

  async findAll(): Promise<WorkItemResponse[]> {
    const [items, displayNames] = await Promise.all([
      this.azureDevOpsService.getWorkItems(),
      this.azureDevOpsService.getUserDisplayNames(),
    ]);

    return items.map((item) => this.mapWorkItem(item, displayNames));
  }

  private mapWorkItem(
    item: AzureDevOpsWorkItem,
    displayNames: Map<string, string>,
  ): WorkItemResponse {
    const fields = item.fields ?? {};
    const parentRelation = item.relations?.find(
      (relation) => relation.rel === 'System.LinkTypes.Hierarchy-Reverse',
    );

    const parentMatch = parentRelation?.url.match(/\/workItems\/(\d+)\/?$/i);

    const assignedToValue = fields['System.AssignedTo'];

    let assignee = 'Unassigned';
    let assigneeEmail: string | undefined;

    if (typeof assignedToValue === 'string') {
      const value = assignedToValue.trim();

      const nameMatch = value.match(/^(.+?)\s*<([^>]+)>$/);

      const matchedName = nameMatch?.[1]?.trim();
      const matchedEmail = nameMatch?.[2]?.trim();

      if (matchedName) {
        assignee = matchedName;
      } else {
        assignee =
          displayNames.get(value.toLowerCase()) || value || 'Unassigned';
      }

      if (matchedEmail) {
        assigneeEmail = matchedEmail;
      } else if (value.includes('@')) {
        assigneeEmail = value;
      }
    } else if (assignedToValue && typeof assignedToValue === 'object') {
      const identity = assignedToValue as Record<string, unknown>;

      const displayName = identity['displayName'];
      const mailAddress = identity['mailAddress'];
      const uniqueName = identity['uniqueName'];

      if (typeof displayName === 'string' && displayName.trim()) {
        assignee = displayName.trim();
      }

      if (typeof mailAddress === 'string' && mailAddress.trim()) {
        assigneeEmail = mailAddress.trim();
      } else if (typeof uniqueName === 'string' && uniqueName.includes('@')) {
        assigneeEmail = uniqueName.trim();
      }
    }

    const rawPriority = Number(fields['Microsoft.VSTS.Common.Priority']);

    const priority: WorkItemResponse['priority'] =
      rawPriority === 1 || rawPriority === 2
        ? 'High'
        : rawPriority === 4
          ? 'Low'
          : 'Medium';

    const organization = process.env.AZURE_DEVOPS_ORG ?? '';
    const project = process.env.AZURE_DEVOPS_PROJECT ?? '';

    return {
      id: item.id,
      title: this.getString(fields['System.Title'], `Item ${item.id}`),
      type: this.getString(fields['System.WorkItemType'], 'Task'),
      state: this.getString(fields['System.State'], 'New'),
      assignedTo: assignee,
      ...(assigneeEmail ? { assignedToEmail: assigneeEmail } : {}),
      priority,
      updatedAt: this.getString(fields['System.ChangedDate'], ''),
      ...(parentMatch ? { parentId: Number(parentMatch[1]) } : {}),
      url:
        `https://dev.azure.com/${encodeURIComponent(organization)}` +
        `/${encodeURIComponent(project)}/_workitems/edit/${item.id}`,
    };
  }

  private getString(value: unknown, fallback: string): string {
    return typeof value === 'string' && value.length > 0 ? value : fallback;
  }
  async create(dto: CreateWorkItemDto): Promise<WorkItemResponse> {
    const createdItem = await this.azureDevOpsService.createWorkItem(dto);

    // Map the response without making another external identity request.
    // The next GET /work-items request will resolve display names.
    return this.mapWorkItem(createdItem, new Map<string, string>());
  }

  async update(id: number, dto: UpdateWorkItemDto): Promise<WorkItemResponse> {
    const updatedItem = await this.azureDevOpsService.updateWorkItem(id, dto);

    // Identity lookup is supplementary; don't fail an update
    // just because the Graph user lookup is temporarily unavailable.
    const displayNames = await this.azureDevOpsService
      .getUserDisplayNames()
      .catch(() => new Map<string, string>());

    return this.mapWorkItem(updatedItem, displayNames);
  }

  async assign(id: number, assignedTo: string): Promise<WorkItemResponse> {
    return this.update(id, { assignedTo });
  }

  async delete(
    id: number,
    dto: DeleteWorkItemDto,
  ): Promise<{ id: number; deleted: boolean; message: string }> {
    if (!dto.confirm) {
      throw new BadRequestException('Explicit confirmation is required.');
    }

    await this.azureDevOpsService.deleteWorkItem(id);

    return {
      id,
      deleted: true,
      message: `Work item #${id} moved to Azure DevOps Recycle Bin.`,
    };
  }
}
