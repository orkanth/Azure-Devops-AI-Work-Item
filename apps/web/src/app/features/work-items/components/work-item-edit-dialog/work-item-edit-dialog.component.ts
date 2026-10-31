import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  WorkItem,
  WorkItemPriority,
  WorkItemState,
  WorkItemType,
} from '../../../../shared/models/work-item.model';

export interface WorkItemEditResult {
  id: number;
  changes: Partial<
    Pick<
      WorkItem,
      | 'title'
      | 'description'
      | 'acceptanceCriteria'
      | 'state'
      | 'assignedTo'
      | 'priority'
    >
  >;
}

@Component({
  selector: 'app-work-item-edit-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './work-item-edit-dialog.component.html',
  styleUrl: './work-item-edit-dialog.component.css',
})
export class WorkItemEditDialogComponent {
  private currentItem: WorkItem | null = null;

  @Input()
  set item(value: WorkItem | null) {
    this.currentItem = value;

    if (value) {
      this.editTitle = value.title;
      this.editDescription = value.description ?? '';
      this.editAcceptanceCriteria = value.acceptanceCriteria ?? '';
      this.editState = value.state;
      this.editAssignee =
        value.assignedToEmail ??
        (value.assignedTo === 'Unassigned' ? '' : value.assignedTo);
      this.editPriority = value.priority;
      this.modalError = '';
    }
  }

  get item(): WorkItem | null {
    return this.currentItem;
  }

  // Retained for compatibility with the existing parent binding.
  @Input() workItemTypes: WorkItemType[] = [];

  @Input() workItemStates: WorkItemState[] = [];
  @Input() priorities: WorkItemPriority[] = [];

  @Output() closed = new EventEmitter<void>();
  @Output() saved = new EventEmitter<WorkItemEditResult>();

  editTitle = '';
  editDescription = '';
  editAcceptanceCriteria = '';
  editState: WorkItemState = 'New';
  editAssignee = '';
  editPriority: WorkItemPriority = 'Medium';
  modalError = '';

  get availableStates(): WorkItemState[] {
    const currentState = this.currentItem?.state;

    return currentState && !this.workItemStates.includes(currentState)
      ? [...this.workItemStates, currentState]
      : this.workItemStates;
  }

  submit(): void {
    const item = this.currentItem;

    if (!item) return;

    const title = this.editTitle.trim();

    if (!title) {
      this.modalError = 'A title is required.';
      return;
    }

    const changes: WorkItemEditResult['changes'] = {
      title,
      description: this.editDescription.trim(),
      state: this.editState,
      priority: this.editPriority,
    };

    if (item.type === 'User Story' || item.type === 'Bug') {
      changes.acceptanceCriteria = this.editAcceptanceCriteria.trim();
    }

    const assignee = this.editAssignee.trim();

    if (assignee) {
      changes.assignedTo = assignee;
    }

    this.saved.emit({
      id: item.id,
      changes,
    });
  }
}