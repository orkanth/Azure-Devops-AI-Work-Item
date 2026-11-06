import { computed, Injectable, signal } from '@angular/core';

import { GeneratedEpic } from '../../../shared/models/generated-board.model';

@Injectable({
  providedIn: 'root',
})
export class GeneratedBoardStore {
  private readonly _generatedEpic = signal<GeneratedEpic | null>(null);
  private readonly _publishId = signal<string | null>(null);

  readonly generatedEpic = this._generatedEpic.asReadonly();
  readonly publishId = this._publishId.asReadonly();

  readonly hasGeneratedBoard = computed(
    () => this._generatedEpic() !== null,
  );

  setGeneratedBoard(epic: GeneratedEpic): void {
    this._generatedEpic.set(epic);
    this._publishId.set(crypto.randomUUID());
  }

  clearGeneratedBoard(): void {
    this._generatedEpic.set(null);
    this._publishId.set(null);
  }
}