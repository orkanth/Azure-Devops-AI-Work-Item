import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ApiHealth {
  status: string;
  service: string;
}

export interface ApiWorkItem {
  id: number;
  type: 'Epic' | 'Feature' | 'User Story' | 'Task' | 'Bug';
  title: string;
  description?: string;
  acceptanceCriteria?: string;
  state: string;
  assignedTo: string;
  assignedToEmail?: string;
  priority: string;
  parentId?: number;
  updatedAt: string;
  url?: string;
}

export interface CreateApiWorkItemRequest {
  type: ApiWorkItem['type'];
  title: string;
  description?: string;
  acceptanceCriteria?: string;
  assignedTo?: string;
  priority?: string;
  parentId?: number;
}

export interface UpdateApiWorkItemRequest {
  title?: string;
  description?: string;
  acceptanceCriteria?: string;
  state?: string;
  assignedTo?: string;
  priority?: string;
}
@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = environment.apiBaseUrl.replace(/\/+$/, '');;

  getHealth(): Observable<ApiHealth> {
    return this.http.get<ApiHealth>(`${this.baseUrl}/health`);
  }
  getWorkItems() {
    return this.http.get<ApiWorkItem[]>(`${this.baseUrl}/work-items`);
  }

  createWorkItem(payload: CreateApiWorkItemRequest) {
    return this.http.post<ApiWorkItem>(
      `${this.baseUrl}/work-items`,
      payload,
    );
  }

  updateWorkItem(id: number, payload: UpdateApiWorkItemRequest) {
    return this.http.patch<ApiWorkItem>(
      `${this.baseUrl}/work-items/${id}`,
      payload,
    );
  }

  deleteWorkItem(id: number) {
    return this.http.delete<{ message?: string }>(
      `${this.baseUrl}/work-items/${id}`,
      {
        body: { confirm: true },
      },
    );
  }
}
