import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { WorkItem } from '../../models/work-item.model';

export type WorkItemTableMode = 'recent' | 'full';

/** Shared table presentation for overview activity and full work-item browsing. */
@Component({
  selector: 'app-work-item-table',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './work-item-table.component.html',
  styleUrl: './work-item-table.component.css',
})
export class WorkItemTableComponent {
  @Input() items: WorkItem[] = [];
  @Input() allItems: WorkItem[] = [];
  @Input() totalCount = 0;
  @Input() mode: WorkItemTableMode = 'recent';
  @Input() showReset = true;

  @Output() readonly editRequested = new EventEmitter<WorkItem>();
  @Output() readonly deleteRequested = new EventEmitter<WorkItem>();
  @Output() readonly resetRequested = new EventEmitter<void>();
  @Output() readonly openAllRequested = new EventEmitter<void>();

  typeClass(type: WorkItem['type']): string {
    return type.toLowerCase().replace(' ', '-');
  }

  typeLetter(type: WorkItem['type']): string {
    if (type === 'User Story') return 'S';
    return type.charAt(0);
  }

  stateClass(state: WorkItem['state']): string {
    return state.toLowerCase().replace(' ', '-');
  }

  initials(name: string): string {
    return name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => (part[0] ?? '').toUpperCase())
      .join('');
  }

  parentTitle(parentId?: number): string {
    if (!parentId) return '—';
    const parent = this.allItems.find((item) => item.id === parentId);
    return parent ? `#${parent.id} ${parent.title}` : '—';
  }
}
