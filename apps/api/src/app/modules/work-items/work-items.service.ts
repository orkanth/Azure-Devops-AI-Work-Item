import { BadRequestException, Injectable } from '@nestjs/common';
import {
  AzureDevOpsService,
  AzureDevOpsWorkItem,
  WorkItemFilters,
} from '../azure-devops/azure-devops.service';
import { CreateWorkItemDto } from './dto/create-work-item.dto';
import { UpdateWorkItemDto } from './dto/update-work-item.dto';
import { DeleteWorkItemDto } from './dto/delete-work-item.dto';
import { PublishEpicDto } from './dto/publish-work-items.dto';
import { NotFoundException } from '@nestjs/common';
import { CreateAzureDevOpsWorkItemInput } from '../azure-devops/azure-devops.service';
import {
  GeneratedWorkItemDto,
  PublishGeneratedWorkItemsDto,
} from './dto/publish-generated-work-items.dto';

export interface WorkItemResponse {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedToEmail?: string;
  assignedTo: string;
  acceptanceCriteria?: string;
  description?: string;
  priority: 'Low' | 'Medium' | 'High';
  updatedAt: string;
  parentId?: number;
  url: string;
}

@Injectable()
export class WorkItemsService {
  private readonly allowedChildren: Record<string, string[]> = {
    Epic: ['Feature', 'User Story', 'Task', 'Bug'],
    Feature: ['User Story', 'Task', 'Bug'],
    'User Story': ['Task', 'Bug'],
    Task: [],
    Bug: [],
  };

  private readonly allowedParents: Record<string, string[]> = {
    Epic: [],
    Feature: ['Epic'],
    'User Story': ['Epic', 'Feature'],
    Task: ['Epic', 'Feature', 'User Story'],
    Bug: ['Epic', 'Feature', 'User Story'],
  };

  constructor(private readonly azureDevOpsService: AzureDevOpsService) {}
  async findAll(filters: WorkItemFilters = {}): Promise<WorkItemResponse[]> {
    const [items, displayNames] = await Promise.all([
      this.azureDevOpsService.getWorkItems(filters),
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
      description: this.getString(fields['System.Description'], ''),
      acceptanceCriteria: this.getString(
        fields['Microsoft.VSTS.Common.AcceptanceCriteria'],
        '',
      ),
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

  async publish(dto: PublishEpicDto) {
    const publishTag = `DevFlowPublish-${dto.publishId}`;

    // Check whether this proposal has already created an Epic.
    const existingEpicIds = await this.azureDevOpsService.findWorkItemIdsByTag(
      publishTag,
      'Epic',
    );

    if (existingEpicIds.length > 0) {
      return {
        success: false,
        status: 'already-published',
        message:
          'This proposal has already created an Epic. ' +
          'No new work items were created.',
        existingEpicId: existingEpicIds[0],
        created: [],
        errors: [],
      };
    }
    const created: Array<{
      id: number;
      type: string;
      title: string;
      parentId?: number;
      url: string;
    }> = [];

    const errors: Array<{
      type: string;
      title: string;
      message: string;
    }> = [];

    const createItem = async (
      input: CreateAzureDevOpsWorkItemInput,
      itemTag: string,
    ): Promise<number | null> => {
      try {
        // Check whether this exact hierarchy item already exists.
        const existingIds = await this.azureDevOpsService.findWorkItemIdsByTag(
          itemTag,
          input.type,
        );

        const existingId = existingIds[0];

        if (existingId !== undefined) {
          return existingId;
        }
        const item = await this.azureDevOpsService.createWorkItem({
          ...input,
          tags: itemTag,
        });

        created.push({
          id: item.id,
          type: input.type,
          title: input.title,
          ...(input.parentId ? { parentId: input.parentId } : {}),
          url: item.url,
        });

        return item.id;
      } catch (error: unknown) {
        errors.push({
          type: input.type,
          title: input.title,
          message:
            error instanceof Error
              ? error.message
              : 'Unknown Azure DevOps error',
        });

        return null;
      }
    };

    // 1. Create the Epic.
    const epicId = await createItem(
      {
        type: 'Epic',
        title: dto.title,
        description: dto.description,
      },
      publishTag,
    );

    // Without an Epic, the hierarchy cannot be created.
    if (epicId === null) {
      return {
        success: false,
        status: 'failed',
        message: 'The Epic could not be created.',
        created,
        errors,
      };
    }

    // 2. Create Features under the Epic.
    for (const [featureIndex, feature] of dto.features.entries()) {
      const featureId = await createItem(
        {
          type: 'Feature',
          title: feature.title,
          description: feature.description,
          parentId: epicId,
        },
        `${publishTag}-Feature-${featureIndex}`,
      );

      if (featureId === null) continue;

      for (const [storyIndex, story] of feature.user_stories.entries()) {
        const storyId = await createItem(
          {
            type: 'User Story',
            title: story.title,
            description: story.description,
            acceptanceCriteria: story.acceptance_criteria.join('\n'),
            parentId: featureId,
          },
          `${publishTag}-Feature-${featureIndex}-Story-${storyIndex}`,
        );

        if (storyId === null) continue;

        for (const [taskIndex, task] of story.tasks.entries()) {
          await createItem(
            {
              type: 'Task',
              title: task.title,
              description: task.description,
              parentId: storyId,
            },
            `${publishTag}-Feature-${featureIndex}-Story-${storyIndex}-Task-${taskIndex}`,
          );
        }
      }
    }

    const success = errors.length === 0;

    return {
      success,
      status: success ? 'completed' : created.length > 0 ? 'partial' : 'failed',
      message: success
        ? 'All work items were published successfully.'
        : 'Publishing finished with errors. Review the results before retrying.',
      created,
      errors,
    };
  }

  async findOne(id: number): Promise<WorkItemResponse> {
    const [item, displayNames] = await Promise.all([
      this.azureDevOpsService.getWorkItemById(id),
      this.azureDevOpsService.getUserDisplayNames(),
    ]);

    if (!item) {
      throw new NotFoundException(`Work item ${id} not found`);
    }

    return this.mapWorkItem(item, displayNames);
  }

  private validateGeneratedHierarchy(
    item: GeneratedWorkItemDto,
    expectedParentType?: string,
  ): void {
    if (
      expectedParentType &&
      !this.allowedChildren[expectedParentType]?.includes(item.type)
    ) {
      throw new BadRequestException(
        `${item.type} cannot be created under ${expectedParentType}.`,
      );
    }

    for (const child of item.children ?? []) {
      this.validateGeneratedHierarchy(child, item.type);
    }
  }

  private async resolveGeneratedParent(
    reference?: string | null,
  ): Promise<AzureDevOpsWorkItem | undefined> {
    if (!reference?.trim()) {
      return undefined;
    }

    const value = reference.trim();

    let matches: AzureDevOpsWorkItem[];

    if (value.startsWith('#')) {
      const id = Number(value.slice(1));

      if (!Number.isInteger(id) || id <= 0) {
        throw new BadRequestException('Invalid parent work item ID.');
      }

      const item = await this.azureDevOpsService.getWorkItemById(id);
      matches = item ? [item] : [];
    } else {
      matches = await this.azureDevOpsService.findWorkItemsByTitle(value);
    }

    if (matches.length === 0) {
      throw new NotFoundException(
        `Parent work item "${value}" was not found in the configured project.`,
      );
    }

    if (matches.length > 1) {
      throw new BadRequestException(
        `Multiple work items match "${value}". Please specify the parent by ID.`,
      );
    }

    const parent = matches[0];

    if (!parent) {
      throw new NotFoundException(`Parent work item "${value}" was not found.`);
    }

    this.validateWorkItemProject(parent);

    return parent;
  }

  async publishGenerated(dto: PublishGeneratedWorkItemsDto) {
    if (!dto.items.every((item) => item.type === dto.requested_type)) {
      throw new BadRequestException(
        'Every root item must match the requested work-item type.',
      );
    }

    // Validate the complete hierarchy before creating anything.
    for (const item of dto.items) {
      this.validateGeneratedHierarchy(item);

      if (dto.parent_reference && !this.allowedParents[item.type]?.length) {
        throw new BadRequestException(
          `${item.type} cannot have a parent work item.`,
        );
      }
    }

    const parent = await this.resolveGeneratedParent(dto.parent_reference);

    if (parent) {
      const parentType = String(parent.fields['System.WorkItemType'] ?? '');

      for (const item of dto.items) {
        if (!this.allowedParents[item.type]?.includes(parentType)) {
          throw new BadRequestException(
            `${item.type} cannot be created under ${parentType}.`,
          );
        }
      }
    }

    const publishTag = `DevFlowPublish-${dto.publishId}`;

    const created: Array<{
      id: number;
      type: string;
      title: string;
      parentId?: number;
      url: string;
    }> = [];

    const reused: Array<{
      id: number;
      type: string;
      title: string;
    }> = [];

    const errors: Array<{
      type: string;
      title: string;
      message: string;
    }> = [];

    const createRecursively = async (
      item: GeneratedWorkItemDto,
      parentId: number | undefined,
      itemTag: string,
    ): Promise<number | null> => {
      try {
        // Check whether this item was already created.
        const existingIds = await this.azureDevOpsService.findWorkItemIdsByTag(
          itemTag,
          item.type,
        );

        const existingId = existingIds[0];

        if (existingId !== undefined) {
          const existingItem =
            await this.azureDevOpsService.getWorkItemById(existingId);

          if (!existingItem) {
            throw new NotFoundException(
              `Existing work item ${existingId} was not found.`,
            );
          }

          this.validateWorkItemProject(existingItem);

          // Validate that the existing item matches the proposal.
          const existingType = String(
            existingItem.fields['System.WorkItemType'] ?? '',
          );

          const existingTitle = String(
            existingItem.fields['System.Title'] ?? '',
          );

          if (existingType !== item.type || existingTitle !== item.title) {
            throw new BadRequestException(
              `Existing work item #${existingId} does not match the publishing proposal.`,
            );
          }

          // Validate its parent relationship.
          const actualParentId = this.getParentIdFromWorkItem(existingItem);

          if (actualParentId !== parentId) {
            throw new BadRequestException(
              `Existing work item #${existingId} has a different parent relationship.`,
            );
          }

          reused.push({
            id: existingId,
            type: item.type,
            title: item.title,
          });

          // IMPORTANT: Process children even when the parent already exists.
          await Promise.all(
            (item.children ?? []).map((child, index) =>
              createRecursively(child, existingId, `${itemTag}-Child-${index}`),
            ),
          );

          return existingId;
        }

        // Create the current work item.
        const createdItem = await this.azureDevOpsService.createWorkItem({
          type: item.type,
          title: item.title,
          description: item.description,
          acceptanceCriteria: item.acceptance_criteria?.join('\n'),
          ...(parentId !== undefined ? { parentId } : {}),
          tags: itemTag,
        });

        created.push({
          id: createdItem.id,
          type: item.type,
          title: item.title,
          ...(parentId !== undefined ? { parentId } : {}),
          url: createdItem.url,
        });

        // Create children under the newly created parent.
        await Promise.all(
          (item.children ?? []).map((child, index) =>
            createRecursively(
              child,
              createdItem.id,
              `${itemTag}-Child-${index}`,
            ),
          ),
        );
        return createdItem.id;
      } catch (error: unknown) {
        errors.push({
          type: item.type,
          title: item.title,
          message:
            error instanceof Error
              ? error.message
              : 'Unknown Azure DevOps error',
        });

        return null;
      }
    };
    // Publish independent root items concurrently.
    await Promise.all(
      dto.items.map((item, index) =>
        createRecursively(item, parent?.id, `${publishTag}-Item-${index}`),
      ),
    );

    // Determine the publishing result.
    const success = errors.length === 0;

    return {
      success,
      status: success
        ? 'completed'
        : created.length > 0 || reused.length > 0
          ? 'partial'
          : 'failed',
      message: success
        ? 'All work items were published successfully to Azure DevOps.'
        : 'Publishing completed with errors. Review the results.',
      requestedType: dto.requested_type,
      created,
      reused,
      errors,
      summary: {
        created: created.length,
        reused: reused.length,
        failed: errors.length,
      },
    };
  }

  private getParentIdFromWorkItem(
    item: AzureDevOpsWorkItem,
  ): number | undefined {
    const relation = item.relations?.find(
      (relation) => relation.rel === 'System.LinkTypes.Hierarchy-Reverse',
    );

    if (!relation) {
      return undefined;
    }

    const segments = new URL(relation.url).pathname.split('/');
    const id = Number(segments[segments.length - 1]);

    return Number.isInteger(id) && id > 0 ? id : undefined;
  }

  private validateWorkItemProject(workItem: AzureDevOpsWorkItem): void {
    const configuredProject = this.azureDevOpsService.getConfiguredProject();

    const actualProject: unknown = workItem.fields?.['System.TeamProject'];

    if (typeof actualProject !== 'string' || !actualProject.trim()) {
      throw new BadRequestException(
        'Unable to validate the work item project.',
      );
    }

    if (actualProject.toLowerCase() !== configuredProject.toLowerCase()) {
      throw new BadRequestException(
        `Work item ${workItem.id} does not belong to the configured project.`,
      );
    }
  }
}
