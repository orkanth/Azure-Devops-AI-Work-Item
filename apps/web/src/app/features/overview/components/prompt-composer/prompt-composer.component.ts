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

  @Output() readonly promptTextChange = new EventEmitter<string>();
  @Output() readonly commandSubmitted = new EventEmitter<void>();

  submit(): void {
    this.commandSubmitted.emit();
  }
}
