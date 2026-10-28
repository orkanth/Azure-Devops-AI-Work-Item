import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  PromptProposal,
  WorkItem,
  WorkItemState,
  WorkItemType,
} from '../../../../shared/models/work-item.model';

@Component({
  selector: 'app-command-proposal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './command-proposal.component.html',
  styleUrl: './command-proposal.component.css',
})
export class CommandProposalComponent {
  @Input() proposal: PromptProposal | null = null;
  @Input() deleteAcknowledged = false;

  @Output() readonly deleteAcknowledgedChange = new EventEmitter<boolean>();
  @Output() readonly candidateSelected = new EventEmitter<WorkItem>();
  @Output() readonly dismissed = new EventEmitter<void>();
  @Output() readonly confirmed = new EventEmitter<void>();

  typeClass(type: WorkItemType): string {
    return type.toLowerCase().replace(' ', '-');
  }

  typeLetter(type: WorkItemType): string {
    return type === 'User Story' ? 'S' : type.charAt(0);
  }

  stateClass(state: WorkItemState): string {
    return state.toLowerCase().replace(' ', '-');
  }
}
