export interface Job {
  id: number;
  title: string;
  description?: string;
  salary?: string;
  location?: string;
  url: string;
  company?: string;
  applied: boolean;
  match_percent?: number;
  emailed_hiring_manager: boolean;
  date_found: string;
}

export interface ExcludedJob {
  id?: number;
  url: string;
  reason?: string;
  query?: string;
  title?: string;
  date_found?: string;
  date_excluded?: string;
}
