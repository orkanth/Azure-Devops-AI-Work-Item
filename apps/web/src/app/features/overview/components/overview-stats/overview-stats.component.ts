import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { WorkItemCounts } from '../../../work-items/data-access/work-item-store';

@Component({
  selector: 'app-overview-stats',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './overview-stats.component.html',
  styleUrl: './overview-stats.component.css',
})
export class OverviewStatsComponent {
  @Input({ required: true }) stats!: WorkItemCounts;

  formatCount(value: number): string {
    return value < 10 ? `0${value}` : String(value);
  }
}
