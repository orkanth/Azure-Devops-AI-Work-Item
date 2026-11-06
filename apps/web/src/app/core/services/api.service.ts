import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient, HttpParams } from '@angular/common/http';
import { WorkItemsQuery } from '../../shared/models/work-items-query.model';
import { GeneratedFeature } from '../../shared/models/generated-board.model';
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
  isContextOnly?: boolean;
}

export interface ApiWorkItemsPage {
  items: ApiWorkItem[];
  total: number;
  page: number;
  pageSize: number;
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
export interface PublishEpicRequest {
  publishId: string;
  title: string;
  description: string;
  features: GeneratedFeature[];
}

export interface PublishWorkItemsResponse {
  success: boolean;
  status: 'completed' | 'partial' | 'failed' | 'already-published';
  message: string;
  existingEpicId?: number;
  created: Array<{
    id: number;
    type: string;
    title: string;
    parentId?: number;
    url: string;
  }>;
  errors: Array<{
    type: string;
    title: string;
    message: string;
  }>;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = environment.apiBaseUrl.replace(/\/+$/, '');

  getHealth(): Observable<ApiHealth> {
    return this.http.get<ApiHealth>(`${this.baseUrl}/health`);
  }
  getWorkItems(query: WorkItemsQuery) {
    let params = new HttpParams()
      .set('page', query.page)
      .set('pageSize', query.pageSize)
      .set('sortBy', query.sortBy ?? 'id')
      .set('sortOrder', query.sortOrder ?? 'DESC');

    if (query.search?.trim()) {
      params = params.set('search', query.search.trim());
    }

    if (query.type) {
      params = params.set('type', query.type);
    }

    if (query.state) {
      params = params.set('state', query.state);
    }

    return this.http.get<ApiWorkItemsPage>(`${this.baseUrl}/work-items`, {
      params,
    });
  }

  createWorkItem(request: CreateApiWorkItemRequest): Observable<ApiWorkItem> {
    return this.http.post<ApiWorkItem>(`${this.baseUrl}/work-items`, request);
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

  publishGeneratedBoard(
    request: PublishEpicRequest,
  ): Observable<PublishWorkItemsResponse> {
    return this.http.post<PublishWorkItemsResponse>(
      `${this.baseUrl}/work-items/publish`,
      request,
    );
  }
}
