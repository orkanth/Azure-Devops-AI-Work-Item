import {
  BadGatewayException,
  BadRequestException,
  Injectable,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { UpdateWorkItemDto } from '../work-items/dto/update-work-item.dto';

export interface AzureDevOpsWorkItem {
  id: number;
  url: string;
  fields: Record<string, unknown>;
  relations?: Array<{
    rel: string;
    url: string;
  }>;
}
interface AzureDevOpsGraphUser {
  displayName?: string;
  mailAddress?: string;
  principalName?: string;
}

interface GraphUsersResponse {
  value?: AzureDevOpsGraphUser[];
}
interface WiqlQueryResponse {
  workItems?: Array<{ id: number }>;
}

interface WorkItemsResponse {
  value?: AzureDevOpsWorkItem[];
}

export type AzureDevOpsWorkItemType =
  | 'Epic'
  | 'Feature'
  | 'User Story'
  | 'Task'
  | 'Bug';

export interface CreateAzureDevOpsWorkItemInput {
  type: AzureDevOpsWorkItemType;
  title: string;
  description?: string;
  assignedTo?: string;
  priority?: 'Low' | 'Medium' | 'High';
  parentId?: number;
}

@Injectable()
export class AzureDevOpsService {
  private readonly logger = new Logger(AzureDevOpsService.name);
  constructor(private readonly config: ConfigService) {}

  async getWorkItems(): Promise<AzureDevOpsWorkItem[]> {
    const organization = this.getRequiredConfig('AZURE_DEVOPS_ORG');
    const project = this.getRequiredConfig('AZURE_DEVOPS_PROJECT');
    const token = this.getRequiredConfig('AZURE_DEVOPS_PAT');
    const apiVersion =
      this.config.get<string>('AZURE_DEVOPS_API_VERSION') || '7.1';

    const baseUrl =
      `https://dev.azure.com/${encodeURIComponent(organization)}` +
      `/${encodeURIComponent(project)}`;

    const authorization = `Basic ${Buffer.from(`:${token}`).toString('base64')}`;

    const headers = {
      Authorization: authorization,
      Accept: 'application/json',
      'Content-Type': 'application/json',
    };

    // Step 1: Retrieve work-item IDs from the configured project.
    const queryParams = new URLSearchParams({
      $top: '200',
      'api-version': apiVersion,
    });

    const queryUrl = `${baseUrl}/_apis/wit/wiql?${queryParams.toString()}`;

    const queryResult = await this.requestJson<WiqlQueryResponse>(
      queryUrl,
      headers,
      {
        method: 'POST',
        body: JSON.stringify({
          query: `
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = @project
            ORDER BY [System.Id] DESC
          `,
        }),
      },
    );

    const ids = [
      ...new Set(
        (queryResult.workItems ?? [])
          .map((item) => item.id)
          .filter((id) => Number.isInteger(id) && id > 0),
      ),
    ];

    if (ids.length === 0) {
      return [];
    }

    // Step 2: Retrieve fields and parent relationships.
    const itemParams = new URLSearchParams({
      ids: ids.join(','),
      $expand: 'relations',
      'api-version': apiVersion,
    });

    const itemsUrl = `${baseUrl}/_apis/wit/workitems?${itemParams.toString()}`;

    const response = await this.requestJson<WorkItemsResponse>(
      itemsUrl,
      headers,
      { method: 'GET' },
    );

    return response.value ?? [];
  }

  private getRequiredConfig(name: string): string {
    const value = this.config.get<string>(name)?.trim();

    if (!value) {
      throw new InternalServerErrorException(
        `Missing required environment variable: ${name}`,
      );
    }

    return value;
  }

  private async requestJson<T>(
    url: string,
    headers: Record<string, string>,
    init: RequestInit,
  ): Promise<T> {
    let response: Response;

    try {
      response = await fetch(url, {
        ...init,
        headers,
      });
    } catch (error: unknown) {
      this.logger.error(
        `Could not reach Azure DevOps: ${
          error instanceof Error ? error.message : 'Unknown network error'
        }`,
      );

      throw new BadGatewayException(
        'Unable to reach Azure DevOps. Check network connectivity.',
      );
    }

    const responseBody = await response.text();

    if (!response.ok) {
      this.logger.error(
        `Azure DevOps returned HTTP ${response.status}: ${responseBody}`,
      );

      if (response.status === 401 || response.status === 403) {
        throw new BadGatewayException(
          'Azure DevOps rejected the request. Check the token, its scopes, ' +
            'and your organization/project access.',
        );
      }

      throw new BadGatewayException(
        `Azure DevOps returned HTTP ${response.status}. ` +
          'Check the NestJS terminal for details.',
      );
    }

    if (!responseBody.trim()) {
      return undefined as T;
    }

    try {
      return JSON.parse(responseBody) as T;
    } catch {
      this.logger.error('Azure DevOps returned an invalid JSON response.');

      throw new BadGatewayException(
        'Azure DevOps returned an invalid JSON response.',
      );
    }
  }

  async getUserDisplayNames(): Promise<Map<string, string>> {
    const organization = this.getRequiredConfig('AZURE_DEVOPS_ORG');
    const token = this.getRequiredConfig('AZURE_DEVOPS_PAT');

    const url = new URL(
      `https://vssps.dev.azure.com/${encodeURIComponent(organization)}` +
        '/_apis/graph/users',
    );

    url.searchParams.set('subjectTypes', 'user');
    url.searchParams.set('api-version', '7.1-preview.1');

    const headers = {
      Authorization: `Basic ${Buffer.from(`:${token}`).toString('base64')}`,
      Accept: 'application/json',
    };

    const response = await this.requestJson<GraphUsersResponse>(
      url.toString(),
      headers,
      { method: 'GET' },
    );

    const displayNames = new Map<string, string>();

    for (const user of response.value ?? []) {
      const name = user.displayName?.trim();

      if (!name) continue;

      for (const identifier of [user.mailAddress, user.principalName]) {
        if (identifier?.trim()) {
          displayNames.set(identifier.trim().toLowerCase(), name);
        }
      }
    }

    return displayNames;
  }

  async createWorkItem(
    input: CreateAzureDevOpsWorkItemInput,
  ): Promise<AzureDevOpsWorkItem> {
    const organization = this.getRequiredConfig('AZURE_DEVOPS_ORG');
    const project = this.getRequiredConfig('AZURE_DEVOPS_PROJECT');
    const token = this.getRequiredConfig('AZURE_DEVOPS_PAT');

    const apiVersion =
      this.config.get<string>('AZURE_DEVOPS_API_VERSION') || '7.1';

    const baseUrl =
      `https://dev.azure.com/${encodeURIComponent(organization)}` +
      `/${encodeURIComponent(project)}`;

    const headers = {
      Authorization: `Basic ${Buffer.from(`:${token}`).toString('base64')}`,
      Accept: 'application/json',
      'Content-Type': 'application/json-patch+json',
    };

    const patch: Array<{
      op: 'add';
      path: string;
      value: unknown;
    }> = [
      {
        op: 'add',
        path: '/fields/System.Title',
        value: input.title.trim(),
      },
    ];

    if (input.description) {
      patch.push({
        op: 'add',
        path: '/fields/System.Description',
        value: input.description,
      });
    }

    if (input.assignedTo) {
      patch.push({
        op: 'add',
        path: '/fields/System.AssignedTo',
        value: input.assignedTo,
      });
    }

    if (input.priority) {
      const priorityMap = {
        High: 1,
        Medium: 3,
        Low: 4,
      };

      patch.push({
        op: 'add',
        path: '/fields/Microsoft.VSTS.Common.Priority',
        value: priorityMap[input.priority],
      });
    }

    // Establish parent-child relationship when a parent is supplied.
    if (input.parentId) {
      patch.push({
        op: 'add',
        path: '/relations/-',
        value: {
          rel: 'System.LinkTypes.Hierarchy-Reverse',
          url: `${baseUrl}/_apis/wit/workItems/${input.parentId}`,
          attributes: {
            comment: 'Created from Azure DevOps AI Work Item Generator',
          },
        },
      });
    }

    const queryParams = new URLSearchParams({
      'api-version': apiVersion,
      $expand: 'relations',
    });

    const url =
      `${baseUrl}/_apis/wit/workitems/$${encodeURIComponent(input.type)}` +
      `?${queryParams.toString()}`;

    return this.requestJson<AzureDevOpsWorkItem>(url, headers, {
      method: 'POST',
      body: JSON.stringify(patch),
    });
  }
  async updateWorkItem(
    id: number,
    input: UpdateWorkItemDto,
  ): Promise<AzureDevOpsWorkItem> {
    const organization = this.getRequiredConfig('AZURE_DEVOPS_ORG');
    const project = this.getRequiredConfig('AZURE_DEVOPS_PROJECT');
    const token = this.getRequiredConfig('AZURE_DEVOPS_PAT');

    const apiVersion =
      this.config.get<string>('AZURE_DEVOPS_API_VERSION') || '7.1';

    const patch: Array<{
      op: 'add';
      path: string;
      value: unknown;
    }> = [];

    if (input.title !== undefined) {
      patch.push({
        op: 'add',
        path: '/fields/System.Title',
        value: input.title.trim(),
      });
    }

    if (input.description !== undefined) {
      patch.push({
        op: 'add',
        path: '/fields/System.Description',
        value: input.description,
      });
    }

    if (input.state !== undefined) {
      patch.push({
        op: 'add',
        path: '/fields/System.State',
        value: input.state,
      });
    }

    if (input.assignedTo !== undefined) {
      patch.push({
        op: 'add',
        path: '/fields/System.AssignedTo',
        value: input.assignedTo,
      });
    }

    if (input.priority !== undefined) {
      const priorityMap = {
        High: 1,
        Medium: 3,
        Low: 4,
      };

      patch.push({
        op: 'add',
        path: '/fields/Microsoft.VSTS.Common.Priority',
        value: priorityMap[input.priority],
      });
    }

    if (patch.length === 0) {
      throw new BadRequestException('No fields provided for update.');
    }

    const baseUrl =
      `https://dev.azure.com/${encodeURIComponent(organization)}` +
      `/${encodeURIComponent(project)}`;

    const params = new URLSearchParams({
      'api-version': apiVersion,
      $expand: 'relations',
    });

    const url = `${baseUrl}/_apis/wit/workitems/${id}?${params.toString()}`;

    const headers = {
      Authorization: `Basic ${Buffer.from(`:${token}`).toString('base64')}`,
      Accept: 'application/json',
      'Content-Type': 'application/json-patch+json',
    };

    return this.requestJson<AzureDevOpsWorkItem>(url, headers, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  }
  async deleteWorkItem(id: number): Promise<void> {
    const organization = this.getRequiredConfig('AZURE_DEVOPS_ORG');
    const project = this.getRequiredConfig('AZURE_DEVOPS_PROJECT');
    const token = this.getRequiredConfig('AZURE_DEVOPS_PAT');

    const apiVersion =
      this.config.get<string>('AZURE_DEVOPS_API_VERSION') || '7.1';

    const baseUrl =
      `https://dev.azure.com/${encodeURIComponent(organization)}` +
      `/${encodeURIComponent(project)}`;

    const params = new URLSearchParams({
      'api-version': apiVersion,
    });

    const url = `${baseUrl}/_apis/wit/workitems/${id}?${params.toString()}`;

    const headers = {
      Authorization: `Basic ${Buffer.from(`:${token}`).toString('base64')}`,
      Accept: 'application/json',
    };

    await this.requestJson<void>(url, headers, { method: 'DELETE' });
  }
}
