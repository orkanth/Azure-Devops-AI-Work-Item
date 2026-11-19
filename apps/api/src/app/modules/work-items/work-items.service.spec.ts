import { WorkItemsService } from './work-items.service';
import { AzureDevOpsService } from '../azure-devops/azure-devops.service';

describe('WorkItemsService - publishGenerated', () => {
  let service: WorkItemsService;

  const itemsByTag = new Map<string, number>();
  const itemsById = new Map<number, any>();

  let nextId = 1000;
  let shouldFailTask = true;

  const azureDevOpsService = {
    getConfiguredProject: jest.fn(() => 'AzureDevOpsAI'),

    findWorkItemIdsByTag: jest.fn(async (tag: string) => {
      const id = itemsByTag.get(tag);
      return id !== undefined ? [id] : [];
    }),

    getWorkItemById: jest.fn(async (id: number) => {
      return itemsById.get(id);
    }),

    createWorkItem: jest.fn(async (input: any) => {
      // Simulate one temporary Azure DevOps failure.
      if (input.title === 'Implement Registration API' && shouldFailTask) {
        shouldFailTask = false;
        throw new Error('Simulated Azure DevOps failure');
      }

      const id = nextId++;

      const item = {
        id,
        url: `https://dev.azure.com/test/project/_workitems/edit/${id}`,
        fields: {
          'System.Id': id,
          'System.Title': input.title,
          'System.WorkItemType': input.type,
          'System.TeamProject': 'AzureDevOpsAI',
        },
        relations:
          input.parentId !== undefined
            ? [
                {
                  rel: 'System.LinkTypes.Hierarchy-Reverse',
                  url: `https://dev.azure.com/test/project/_apis/wit/workItems/${input.parentId}`,
                },
              ]
            : [],
      };

      itemsByTag.set(input.tags, id);
      itemsById.set(id, item);

      return item;
    }),
  };

  const proposal = {
    publishId: 'test-publish-123',
    requested_type: 'Epic' as const,
    parent_reference: null,
    items: [
      {
        type: 'Epic' as const,
        title: 'User Management',
        description: 'Manage users in DevFlow AI.',
        acceptance_criteria: [],
        children: [
          {
            type: 'Feature' as const,
            title: 'User Registration',
            description: 'Register new users.',
            acceptance_criteria: [],
            children: [
              {
                type: 'User Story' as const,
                title: 'Register an account',
                description: 'As a user, I want to register.',
                acceptance_criteria: [],
                children: [
                  {
                    type: 'Task' as const,
                    title: 'Implement Registration API',
                    description: 'Create the registration API.',
                    acceptance_criteria: [],
                    children: [],
                  },
                  {
                    type: 'Task' as const,
                    title: 'Implement Registration Form',
                    description: 'Create the registration form.',
                    acceptance_criteria: [],
                    children: [],
                  },
                ],
              },
            ],
          },
        ],
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();

    itemsByTag.clear();
    itemsById.clear();

    nextId = 1000;
    shouldFailTask = true;

    service = new WorkItemsService(
      azureDevOpsService as unknown as AzureDevOpsService,
    );
  });

  it('should report partial success when one task fails', async () => {
    const result = await service.publishGenerated(proposal);

    expect(result.status).toBe('partial');
    expect(result.success).toBe(false);

    expect(result.summary.created).toBe(4);
    expect(result.summary.reused).toBe(0);
    expect(result.summary.failed).toBe(1);

    expect(result.errors[0]?.title).toBe('Implement Registration API');
  });

  it('should reuse successful items and retry only the failed task', async () => {
    // First publishing attempt.
    const firstResult = await service.publishGenerated(proposal);

    expect(firstResult.status).toBe('partial');

    // Retry with exactly the same publishId and proposal.
    const retryResult = await service.publishGenerated(proposal);

    expect(retryResult.status).toBe('completed');
    expect(retryResult.success).toBe(true);

    expect(retryResult.summary.created).toBe(1);
    expect(retryResult.summary.reused).toBe(4);
    expect(retryResult.summary.failed).toBe(0);

    expect(retryResult.errors).toHaveLength(0);

    expect(retryResult.created[0]?.title).toBe('Implement Registration API');

    // 5 calls on first attempt + 1 retry.
    expect(azureDevOpsService.createWorkItem).toHaveBeenCalledTimes(6);
  });

  it('should reject an invalid work item hierarchy before publishing', async () => {
    const invalidProposal = {
      publishId: 'invalid-hierarchy-test',
      requested_type: 'Epic' as const,
      parent_reference: null,
      items: [
        {
          type: 'Epic' as const,
          title: 'Invalid Hierarchy Test',
          description: 'Test invalid hierarchy validation.',
          acceptance_criteria: [],
          children: [
            {
              type: 'Task' as const,
              title: 'Parent Task',
              description: 'Parent task.',
              acceptance_criteria: [],
              children: [
                {
                  type: 'Task' as const,
                  title: 'Child Task',
                  description: 'Invalid child task.',
                  acceptance_criteria: [],
                  children: [],
                },
              ],
            },
          ],
        },
      ],
    };

    await expect(service.publishGenerated(invalidProposal)).rejects.toThrow(
      'Task cannot be created under Task.',
    );

    // Validation must happen before any Azure DevOps publishing call.
    expect(azureDevOpsService.createWorkItem).not.toHaveBeenCalled();
  });

  it('should reject an existing work item with a different parent', async () => {
    const publishId = 'invalid-parent-test';

    // Simulate an existing Feature with the expected publishing tag.
    const existingFeatureId = 900;
    const featureTag = `DevFlowPublish-${publishId}-Item-0-Child-0`;

    itemsByTag.set(featureTag, existingFeatureId);

    // This Feature belongs to Epic #999, not the Epic
    // that this publishing operation will create.
    itemsById.set(existingFeatureId, {
      id: existingFeatureId,
      fields: {
        'System.Title': 'User Registration',
        'System.WorkItemType': 'Feature',
        'System.TeamProject': 'AzureDevOpsAI',
      },
      relations: [
        {
          rel: 'System.LinkTypes.Hierarchy-Reverse',
          url: 'https://dev.azure.com/test/project/_apis/wit/workItems/999',
        },
      ],
    });

    const invalidParentProposal = {
      ...proposal,
      publishId,
    };

    const result = await service.publishGenerated(invalidParentProposal);

    expect(result.status).toBe('partial');
    expect(result.success).toBe(false);

    // The Epic was created successfully.
    expect(result.summary.created).toBe(1);

    // The existing Feature was not reused.
    expect(result.summary.reused).toBe(0);

    // The incorrect parent relationship was rejected.
    expect(result.summary.failed).toBe(1);

    expect(result.errors[0]?.title).toBe('User Registration');

    expect(result.errors[0]?.message).toContain(
      'has a different parent relationship',
    );

    // Only the Epic should have been created.
    expect(azureDevOpsService.createWorkItem).toHaveBeenCalledTimes(1);
  });

  it('should stop publishing when Epic creation fails', async () => {
    // Simulate Azure DevOps connection failure.
    azureDevOpsService.createWorkItem.mockRejectedValueOnce(
      new Error('Could not reach Azure DevOps: fetch failed'),
    );

    const result = await service.publishGenerated(proposal);

    expect(result.status).toBe('failed');
    expect(result.success).toBe(false);

    expect(result.summary.created).toBe(0);
    expect(result.summary.reused).toBe(0);
    expect(result.summary.failed).toBe(1);

    expect(result.errors[0]?.type).toBe('Epic');

    expect(result.errors[0]?.message).toContain('Could not reach Azure DevOps');

    // No Features, Stories or Tasks should be attempted.
    expect(azureDevOpsService.createWorkItem).toHaveBeenCalledTimes(1);
  });
});
