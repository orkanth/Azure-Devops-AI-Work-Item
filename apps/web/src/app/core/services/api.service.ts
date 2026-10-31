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
  title: string;
  type: string;
  state: string;
  assignedTo: string;
  priority: string;
  updatedAt: string;
  parentId?: number;
  url: string;
}
export interface ApiWorkItem {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedTo: string;
  assignedToEmail?: string;
  priority: string;
  updatedAt: string;
  parentId?: number;
  url: string;
}
@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = environment.apiBaseUrl;

  getHealth(): Observable<ApiHealth> {
    return this.http.get<ApiHealth>(`${this.baseUrl}/health`);
  }
getWorkItems(): Observable<ApiWorkItem[]> {
  return this.http.get<ApiWorkItem[]>(
    `${this.baseUrl}/work-items`,
  );
}
}
