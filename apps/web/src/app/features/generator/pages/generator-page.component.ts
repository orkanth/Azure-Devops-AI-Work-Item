
import { Component, inject, signal } from '@angular/core';  
import { BoardGenerationService } from '../data-access/board-generation.service';
import { GeneratedEpic } from '../../../shared/models/generated-board.model';

@Component({
  selector: 'app-generator-page',
  standalone: true,
  templateUrl: './generator-page.component.html',
  styleUrl: './generator-page.component.css',
})
export class GeneratorPageComponent {
  private readonly boardGenerationService = inject(BoardGenerationService);

  readonly requirement = signal('');
  readonly generatedEpic = signal<GeneratedEpic | null>(null);
  readonly isGenerating = signal(false);
  readonly errorMessage = signal<string | null>(null);

  async generateBoard(): Promise<void> {
    const requirement = this.requirement().trim();

    if (!requirement || requirement.length < 10) {
      this.errorMessage.set(
        'Please enter a requirement with at least 10 characters.',
      );
      return;
    }

    this.isGenerating.set(true);
    this.errorMessage.set(null);
    this.generatedEpic.set(null);

    try {
      const response = await this.boardGenerationService.generateBoard({
        requirement,
      });

      if (!response.epic) {
        throw new Error('The AI did not return a generated Epic.');
      }

      this.generatedEpic.set(response.epic);
    } catch (error) {
      console.error('Board generation failed:', error);

      this.errorMessage.set(
        'Unable to generate the board. Please try again.',
      );
    } finally {
      this.isGenerating.set(false);
    }
  }
}
