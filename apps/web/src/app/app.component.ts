import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MockWorkItemService } from './core/services/mock-work-item.service';
import { PromptCommandService } from './core/services/prompt-command.service';
import { PromptProposal, WorkItem, WorkItemPriority, WorkItemState, WorkItemType } from './shared/models/work-item.model';

type ViewKey = 'overview' | 'work-items' | 'documents' | 'integrations';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly workItemService = inject(MockWorkItemService);
  private readonly promptService = inject(PromptCommandService);

  readonly view = signal<ViewKey>('overview');
  readonly items = this.workItemService.items;
  readonly stats = computed(() => this.workItemService.getCounts());
  readonly workItemTypes: WorkItemType[] = ['Epic', 'Feature', 'User Story', 'Task'];
  readonly workItemStates: WorkItemState[] = ['New', 'Active', 'Resolved', 'Closed'];
  readonly priorities: WorkItemPriority[] = ['Low', 'Medium', 'High'];
  readonly samplePrompts = [
    'Create a user story for password reset',
    'Assign task #104 to Alex Morgan',
    'Move API validation to Done',
    'Delete task #106',
  ];

  promptText = '';
  searchTerm = '';
  typeFilter = 'All types';
  stateFilter = 'All states';
  uploadedFileName = '';
  uploadMessage = '';
  notice = '';
  noticeKind: 'success' | 'info' | 'error' = 'info';
  pendingProposal: PromptProposal | null = null;
  deleteAcknowledged = false;
  editingItem: WorkItem | null = null;
  editTitle = '';
  editType: WorkItemType = 'Task';
  editState: WorkItemState = 'New';
  editAssignee = '';
  editPriority: WorkItemPriority = 'Medium';
  modalError = '';
  readonly currentYear = new Date().getFullYear();

  get filteredItems(): WorkItem[] {
    const query = this.searchTerm.trim().toLowerCase();
    return this.items().filter((item) => {
      const matchesSearch = !query || `${item.id} ${item.title} ${item.assignedTo} ${item.type}`.toLowerCase().includes(query);
      const matchesType = this.typeFilter === 'All types' || item.type === this.typeFilter;
      const matchesState = this.stateFilter === 'All states' || item.state === this.stateFilter;
      return matchesSearch && matchesType && matchesState;
    });
  }

  get visibleTitle(): string {
    const titles: Record<ViewKey, string> = {
      overview: 'AI command center',
      'work-items': 'Work items',
      documents: 'Documents & knowledge',
      integrations: 'Integrations',
    };
    return titles[this.view()];
  }

  openView(view: ViewKey): void {
    this.view.set(view);
    this.notice = '';
  }

  fillPrompt(prompt: string): void {
    this.promptText = prompt;
    this.view.set('overview');
  }

  startCreatePrompt(): void {
    this.view.set('overview');
    this.promptText = 'Create a task for ';
  }

  initials(name: string): string {
    return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => (part[0] ?? '').toUpperCase()).join('');
  }

  submitPrompt(): void {
    if (!this.promptText.trim()) return;
    this.pendingProposal = this.promptService.interpret(this.promptText, this.items());
    this.deleteAcknowledged = false;
    this.notice = '';
  }

  selectCandidate(item: WorkItem): void {
    if (!this.pendingProposal || this.pendingProposal.kind !== 'ambiguous' || !this.pendingProposal.actionKind) return;
    const actionKind = this.pendingProposal.actionKind;
    this.pendingProposal = {
      ...this.pendingProposal,
      kind: actionKind,
      target: item,
      candidates: undefined,
      error: undefined,
      description: this.describeSelectedTarget(actionKind, item, this.pendingProposal),
    };
    this.deleteAcknowledged = false;
  }

  dismissProposal(): void {
    this.pendingProposal = null;
    this.deleteAcknowledged = false;
  }

  applyProposal(): void {
    const proposal = this.pendingProposal;
    if (!proposal || ['unknown', 'ambiguous'].includes(proposal.kind)) return;

    if (proposal.kind === 'create' && proposal.newItem?.type && proposal.newItem.title) {
      const created = this.workItemService.create({
        type: proposal.newItem.type as WorkItemType,
        title: proposal.newItem.title,
        state: (proposal.newItem.state as WorkItemState) ?? 'New',
        assignedTo: proposal.newItem.assignedTo ?? 'Unassigned',
        priority: (proposal.newItem.priority as WorkItemPriority) ?? 'Medium',
        parentId: proposal.newItem.parentId,
      });
      this.finishAction(`Created demo ${created.type} #${created.id}: ${created.title}`);
      return;
    }

    if (!proposal.target) return;
    if (proposal.kind === 'delete') {
      if (!this.deleteAcknowledged) return;
      const title = proposal.target.title;
      const id = proposal.target.id;
      this.workItemService.delete(id);
      this.finishAction(`Deleted demo work item #${id}: ${title}. Direct child items were kept and detached from the deleted parent in this local demo.`);
      return;
    }
    if (proposal.kind === 'assign' && proposal.assignee) {
      this.workItemService.update(proposal.target.id, { assignedTo: proposal.assignee });
      this.finishAction(`Assigned demo work item #${proposal.target.id} to ${proposal.assignee}`);
      return;
    }
    if (proposal.kind === 'update' && proposal.changes) {
      this.workItemService.update(proposal.target.id, proposal.changes);
      this.finishAction(`Updated demo work item #${proposal.target.id}`);
    }
  }

  private finishAction(message: string): void {
    this.pendingProposal = null;
    this.deleteAcknowledged = false;
    this.promptText = '';
    this.noticeKind = 'success';
    this.notice = `${message}. Changes are currently saved only in this browser demo; Azure DevOps is not connected.`;
  }

  prepareDelete(item: WorkItem): void {
    this.pendingProposal = {
      kind: 'delete',
      target: item,
      description: `Delete ${item.type} #${item.id}: “${item.title}”`,
    };
    this.deleteAcknowledged = false;
    this.notice = '';
    this.view.set('work-items');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  startEdit(item: WorkItem): void {
    this.editingItem = { ...item };
    this.editTitle = item.title;
    this.editType = item.type;
    this.editState = item.state;
    this.editAssignee = item.assignedTo;
    this.editPriority = item.priority;
    this.modalError = '';
  }

  closeEdit(): void {
    this.editingItem = null;
    this.modalError = '';
  }

  saveEdit(): void {
    if (!this.editingItem) return;
    if (!this.editTitle.trim()) {
      this.modalError = 'A title is required.';
      return;
    }
    if (!this.editAssignee.trim()) {
      this.modalError = 'Enter a person name or use Unassigned.';
      return;
    }
    this.workItemService.update(this.editingItem.id, {
      title: this.editTitle.trim(),
      type: this.editType,
      state: this.editState,
      assignedTo: this.editAssignee.trim(),
      priority: this.editPriority,
    });
    this.closeEdit();
    this.noticeKind = 'success';
    this.notice = 'Work item updated in local demo data. Azure DevOps is not connected yet.';
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const supported = /\.(docx|pdf)$/i.test(file.name);
    if (!supported) {
      this.uploadedFileName = '';
      this.uploadMessage = 'Choose a Word (.docx) or PDF file.';
      input.value = '';
      return;
    }
    this.uploadedFileName = file.name;
    this.uploadMessage = 'File selected. Document extraction and RAG ingestion will be enabled when the AI service is connected.';
  }

  clearUpload(): void {
    this.uploadedFileName = '';
    this.uploadMessage = '';
  }

  resetDemo(): void {
    this.workItemService.reset();
    this.pendingProposal = null;
    this.noticeKind = 'info';
    this.notice = 'Sample work items restored.';
    this.searchTerm = '';
    this.typeFilter = 'All types';
    this.stateFilter = 'All states';
  }

  typeClass(type: WorkItemType): string {
    return type.toLowerCase().replace(' ', '-');
  }

  stateClass(state: WorkItemState): string {
    return state.toLowerCase().replace(' ', '-');
  }

  parentTitle(parentId?: number): string {
    if (!parentId) return '—';
    const parent = this.workItemService.findById(parentId);
    return parent ? `#${parent.id} ${parent.title}` : '—';
  }

  private describeSelectedTarget(kind: PromptProposal['actionKind'], item: WorkItem, previous: PromptProposal): string {
    if (kind === 'delete') return `Delete ${item.type} #${item.id}: “${item.title}”`;
    if (kind === 'assign') return `Assign ${item.type} #${item.id} to ${previous.assignee ?? 'the selected user'}`;
    if (kind === 'update') {
      if (previous.changes?.state) return `Set ${item.type} #${item.id} to ${previous.changes.state}`;
      if (previous.changes?.title) return `Rename ${item.type} #${item.id} to “${previous.changes.title}”`;
      return `Update ${item.type} #${item.id}`;
    }
    return previous.description;
  }
}
