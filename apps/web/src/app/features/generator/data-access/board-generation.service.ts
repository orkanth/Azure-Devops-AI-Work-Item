
import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  GenerateBoardRequest,
  GenerateBoardResponse,
} from '../../../shared/models/generated-board.model';

@Injectable({
  providedIn: 'root',
})
export class BoardGenerationService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://localhost:3000/api/generation/board';

  generateBoard(
    request: GenerateBoardRequest,
  ): Promise<GenerateBoardResponse> {
    return firstValueFrom(
      this.http.post<GenerateBoardResponse>(
        this.apiUrl,
        request,
      ),
    );
  }
}
