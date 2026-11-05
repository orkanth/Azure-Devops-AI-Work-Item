import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-prompt-composer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './prompt-composer.component.html',
  styleUrl: './prompt-composer.component.css',
})
export class PromptComposerComponent {
  @Input() promptText = '';
  @Input() samplePrompts: string[] = [];

  // Configurable presentation
  @Input() title = 'What would you like to do?';

  @Input() description = 'Describe your request in plain English.';
  @Input() buttonLabel = 'Send';
  @Input() placeholder = 'Describe a work item action...';
  @Input() badgeLabel = 'AI COMMANDS';

  @Output() readonly promptTextChange = new EventEmitter<string>();
  @Output() readonly commandSubmitted = new EventEmitter<void>();
  @Input() isLoading = false;
  submit(): void {
    if (this.isLoading || !this.promptText.trim()) {
      return;
    }

    this.commandSubmitted.emit();
  }
}
