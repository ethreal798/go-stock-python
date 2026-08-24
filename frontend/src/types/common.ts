export interface PageResult<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiResponse<T = unknown> {
  status: number;
  message?: string;
  data: T;
}
