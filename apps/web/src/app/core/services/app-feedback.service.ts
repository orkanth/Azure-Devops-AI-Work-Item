import { Injectable, signal } from '@angular/core';

export type FeedbackKind = 'success' | 'info' | 'error';

@Injectable({ providedIn: 'root' })
export class AppFeedbackService {
  readonly message = signal('');
  readonly kind = signal<FeedbackKind>('info');

  show(message: string, kind: FeedbackKind = 'info'): void {
    this.message.set(message);
    this.kind.set(kind);
  }

  clear(): void {
    this.message.set('');
  }
}
