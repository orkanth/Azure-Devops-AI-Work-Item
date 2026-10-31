export type WorkItemSortField =
  | 'id'
  | 'title'
  | 'state'
  | 'priority';

export interface WorkItemsQuery {
  page: number;
  pageSize: number;
  search?: string;
  type?: string;
  state?: string;
  sortBy?: WorkItemSortField;
  sortOrder?: 'ASC' | 'DESC';
}