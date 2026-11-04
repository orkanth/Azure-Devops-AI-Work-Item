import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  GenerateWorkItemsRequest,
  GenerateWorkItemsResponse,
} from '../models/ai-work-item-proposal.model';

@Injectable({
  providedIn: 'root',
})
export class AiWorkItemProposalService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://localhost:8000/api/v1/work-items/generate';

  generateProposal(
    request: GenerateWorkItemsRequest,
  ): Promise<GenerateWorkItemsResponse> {
    return firstValueFrom(
      this.http.post<GenerateWorkItemsResponse>(
        this.apiUrl,
        request,
      ),
    );
  }
}