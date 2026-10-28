import { Component, computed, effect, inject } from '@angular/core';
import { AppFeedbackService } from '../../../core/services/app-feedback.service';
import { PromptCommandService } from '../../../core/services/prompt-command.service';
import { WorkspaceNavigationService } from '../../../core/services/workspace-navigation.service';
import { WorkItemTableComponent } from '../../../shared/components/work-item-table/work-item-table.component';
import {
  PromptProposal,
  WorkItem,
  WorkItemPriority,
  WorkItemState,
  WorkItemType,
} from '../../../shared/models/work-item.model';
import { WORK_ITEM_STORE } from '../../work-items/data-access/work-item-store';
import { CommandProposalComponent } from '../components/command-proposal/command-proposal.component';
import { OverviewStatsComponent } from '../components/overview-stats/overview-stats.component';
import { PromptComposerComponent } from '../components/prompt-composer/prompt-composer.component';

@Component({
  selector: 'app-overview-page',
  standalone: true,
  imports: [
    CommandProposalComponent,
    OverviewStatsComponent,
    PromptComposerComponent,
    WorkItemTableComponent,
  ],
  templateUrl: './overview-page.component.html',
  styleUrl: './overview-page.component.css',
})
export class OverviewPageComponent {
  private readonly workItemStore = inject(WORK_ITEM_STORE);
  private readonly promptService = inject(PromptCommandService);
  private readonly feedback = inject(AppFeedbackService);
  private readonly navigation = inject(WorkspaceNavigationService);

  constructor() {
    effect(() => {
      const prompt = this.navigation.promptSeed();
      if (prompt) {
        this.promptText = prompt;
        this.navigation.clearPromptSeed();
      }
    });
  }

  readonly items = this.workItemStore.items;
  readonly stats = computed(() => this.workItemStore.getCounts());
  readonly samplePrompts: string[] = [
    'Create a user story for password reset',
    'Assign task #104 to Alex Morgan',
    'Move API validation to Done',
    'Delete task #106',
  ];

  promptText = '';
  pendingProposal: PromptProposal | null = null;
  deleteAcknowledged = false;

  navigateToWorkItems(): void {
    this.navigation.navigateTo('work-items');
  }

  startEdit(item: WorkItem): void {
    this.navigation.requestEdit(item);
  }

  submitPrompt(): void {
    if (!this.promptText.trim()) return;

    this.pendingProposal = this.promptService.interpret(this.promptText, this.items());
    this.deleteAcknowledged = false;
    this.feedback.clear();
  }

  selectCandidate(item: WorkItem): void {
    const proposal = this.pendingProposal;
    if (!proposal || proposal.kind !== 'ambiguous' || !proposal.actionKind) return;

    const actionKind = proposal.actionKind;
    this.pendingProposal = {
      ...proposal,
      kind: actionKind,
      target: item,
      candidates: undefined,
      error: undefined,
      description: this.describeSelectedTarget(actionKind, item, proposal),
    };
    this.deleteAcknowledged = false;
  }

  dismissProposal(): void {
    this.pendingProposal = null;
    this.deleteAcknowledged = false;
  }

  async applyProposal(): Promise<void> {
    const proposal = this.pendingProposal;
    if (!proposal || ['unknown', 'ambiguous'].includes(proposal.kind)) return;

    try {
      if (proposal.kind === 'create' && proposal.newItem?.type && proposal.newItem.title) {
        const created = await this.workItemStore.create({
          type: proposal.newItem.type,
          title: proposal.newItem.title,
          state: proposal.newItem.state ?? 'New',
          assignedTo: proposal.newItem.assignedTo ?? 'Unassigned',
          priority: proposal.newItem.priority ?? 'Medium',
          parentId: proposal.newItem.parentId,
        });
        this.finishAction(`Created demo ${created.type} #${created.id}: ${created.title}`);
        return;
      }

      if (!proposal.target) return;

      if (proposal.kind === 'delete') {
        if (!this.deleteAcknowledged) return;
        const { id, title } = proposal.target;
        await this.workItemStore.delete(id);
        this.finishAction(
          `Deleted demo work item #${id}: ${title}. Child items were kept and detached from the deleted parent`,
        );
        return;
      }

      if (proposal.kind === 'assign' && proposal.assignee) {
        await this.workItemStore.update(proposal.target.id, {
          assignedTo: proposal.assignee,
        });
        this.finishAction(`Assigned demo work item #${proposal.target.id} to ${proposal.assignee}`);
        return;
      }

      if (proposal.kind === 'update' && proposal.changes) {
        await this.workItemStore.update(proposal.target.id, proposal.changes);
        this.finishAction(`Updated demo work item #${proposal.target.id}`);
      }
    } catch {
      this.feedback.show(
        'The work-item change could not be completed. Please review the request and try again.',
        'error',
      );
    }
  }

  private finishAction(message: string): void {
    this.pendingProposal = null;
    this.deleteAcknowledged = false;
    this.promptText = '';
    this.feedback.show(
      `${message}. Changes are currently saved only in this browser demo; Azure DevOps is not connected.`,
      'success',
    );
  }

  private describeSelectedTarget(
    kind: PromptProposal['actionKind'],
    item: WorkItem,
    previous: PromptProposal,
  ): string {
    if (kind === 'delete') return `Delete ${item.type} #${item.id}: “${item.title}”`;
    if (kind === 'assign') {
      return `Assign ${item.type} #${item.id} to ${previous.assignee ?? 'the selected user'}`;
    }
    if (kind === 'update') {
      if (previous.changes?.state) {
        return `Set ${item.type} #${item.id} to ${previous.changes.state}`;
      }
      if (previous.changes?.title) {
        return `Rename ${item.type} #${item.id} to “${previous.changes.title}”`;
      }
      return `Update ${item.type} #${item.id}`;
    }
    return previous.description;
  }
}
