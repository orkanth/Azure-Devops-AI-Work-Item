
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

  // Pagination
  @Input() currentPage = 1;
  @Input() pageSize = 10;

  @Output() readonly pageChange = new EventEmitter<number>();

  @Output() readonly editRequested = new EventEmitter<WorkItem>();
  @Output() readonly deleteRequested = new EventEmitter<WorkItem>();
  @Output() readonly resetRequested = new EventEmitter<void>();
  @Output() readonly openAllRequested = new EventEmitter<void>();

  get totalPages(): number {
    return Math.ceil(this.totalCount / this.pageSize);
  }

  get pageNumbers(): number[] {
    return Array.from(
      { length: this.totalPages },
      (_, index) => index + 1,
    );
  }

  get startRecord(): number {
    return this.totalCount === 0
      ? 0
      : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endRecord(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalCount);
  }

  goToPage(page: number): void {
    if (
      page < 1 ||
      page > this.totalPages ||
      page === this.currentPage
    ) {
      return;
    }

    this.pageChange.emit(page);
  }

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
