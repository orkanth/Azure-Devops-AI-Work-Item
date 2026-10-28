import { CommonModule } from '@angular/common';
import { Component, inject, Input, OnInit, signal } from '@angular/core';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app-header.component.html',
  styleUrl: './app-header.component.css',
})
export class AppHeaderComponent implements OnInit {
  @Input() title = 'AI command center';

  private readonly apiService = inject(ApiService);

  readonly apiStatus = signal<'checking' | 'online' | 'offline'>('checking');
  readonly apiError = signal('');

  ngOnInit(): void {
    this.checkApiConnection();
  }

  checkApiConnection(): void {
    this.apiStatus.set('checking');
    this.apiError.set('');

    this.apiService.getHealth().subscribe({
      next: () => {
        this.apiStatus.set('online');
      },
      error: (error: unknown) => {
        this.apiStatus.set('offline');
        this.apiError.set(
          'Cannot connect to the NestJS API. Check that the API is running and CORS allows the frontend origin.',
        );
        console.error('API health check failed:', error);
      },
    });
  }
}
