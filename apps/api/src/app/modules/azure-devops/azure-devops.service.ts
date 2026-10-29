import {
  BadGatewayException,
  Injectable,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export interface AzureDevOpsWorkItem {
  id: number;
  url: string;
  fields: Record<string, unknown>;
  relations?: Array<{
    rel: string;
    url: string;
  }>;
}

interface WiqlQueryResponse {
  workItems?: Array<{ id: number }>;
}

interface WorkItemsResponse {
  value?: AzureDevOpsWorkItem[];
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

  try {
    return JSON.parse(responseBody) as T;
  } catch {
    this.logger.error('Azure DevOps returned an invalid JSON response.');

    throw new BadGatewayException(
      'Azure DevOps returned an invalid JSON response.',
    );
  }
}
}
