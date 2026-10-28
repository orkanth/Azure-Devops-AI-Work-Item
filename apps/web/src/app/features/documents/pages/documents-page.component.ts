import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { AppFeedbackService } from '../../../core/services/app-feedback.service';

@Component({
  selector: 'app-documents-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './documents-page.component.html',
  styleUrl: './documents-page.component.css',
})
export class DocumentsPageComponent {
  private readonly feedback = inject(AppFeedbackService);

  uploadedFileName = '';
  uploadMessage = '';

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (!/\.(docx|pdf)$/i.test(file.name)) {
      this.uploadedFileName = '';
      this.uploadMessage = 'Choose a Word (.docx) or PDF file.';
      input.value = '';
      return;
    }

    this.uploadedFileName = file.name;
    this.uploadMessage =
      'File selected. Document extraction and RAG ingestion will be enabled when the AI service is connected.';
    this.feedback.clear();
  }

  clearUpload(): void {
    this.uploadedFileName = '';
    this.uploadMessage = '';
  }
}
