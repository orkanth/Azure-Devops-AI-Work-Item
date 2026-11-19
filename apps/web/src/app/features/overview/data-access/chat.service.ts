import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ChatRequest, ChatResponse } from '../models/chat.model';
 
@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = environment.apiBaseUrl.replace(/\/+$/, '');

  sendMessage(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(
      `${this.baseUrl}/chat`,
      request,
    );
  }
}