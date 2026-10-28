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
  changes: Partial<Pick<WorkItem, 'title' | 'type' | 'state' | 'assignedTo' | 'priority'>>;
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
      this.editType = value.type;
      this.editState = value.state;
      this.editAssignee = value.assignedTo;
      this.editPriority = value.priority;
      this.modalError = '';
    }
  }

  get item(): WorkItem | null {
    return this.currentItem;
  }

  @Input() workItemTypes: WorkItemType[] = [];
  @Input() workItemStates: WorkItemState[] = [];
  @Input() priorities: WorkItemPriority[] = [];

  @Output() closed = new EventEmitter<void>();
  @Output() saved = new EventEmitter<WorkItemEditResult>();

  editTitle = '';
  editType: WorkItemType = 'Task';
  editState: WorkItemState = 'New';
  editAssignee = '';
  editPriority: WorkItemPriority = 'Medium';
  modalError = '';

  submit(): void {
    const item = this.currentItem;
    if (!item) return;

    const title = this.editTitle.trim();
    const assignedTo = this.editAssignee.trim();

    if (!title) {
      this.modalError = 'A title is required.';
      return;
    }

    if (!assignedTo) {
      this.modalError = 'Enter a person name or use Unassigned.';
      return;
    }

    this.saved.emit({
      id: item.id,
      changes: {
        title,
        type: this.editType,
        state: this.editState,
        assignedTo,
        priority: this.editPriority,
      },
    });
  }
}
