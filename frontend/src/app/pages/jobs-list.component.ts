import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Job, ExcludedJob } from '../models/job.model';

@Component({
  selector: 'app-jobs-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './jobs-list.component.html',
  styleUrl: './jobs-list.component.css',
})
export class JobsListComponent implements OnInit {
  jobs: Job[] = [];
  excludedJobs: ExcludedJob[] = [];
  excludedJobUrls: Set<string> = new Set();
  loading = true;
  error: string | null = null;

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchJobs();
    this.fetchExcludedJobs();
  }

  private fetchJobs(): void {
    this.http.get<Job[]>(`${this.apiUrl}/jobs`).subscribe({
      next: (data) => {
        this.jobs = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load jobs';
        console.error(err);
        this.loading = false;
      },
    });
  }

  private fetchExcludedJobs(): void {
    this.http.get<ExcludedJob[]>(`${this.apiUrl}/excludedJobs`).subscribe({
      next: (data) => {
        this.excludedJobs = data;
        this.excludedJobUrls = new Set(data.map((job) => job.url));
      },
      error: (err) => {
        console.error('Failed to load excluded jobs', err);
      },
    });
  }

  isJobExcluded(job: Job): boolean {
    return this.excludedJobUrls.has(job.url);
  }

  getAvailableJobs(): Job[] {
    return this.jobs.filter((job) => !this.isJobExcluded(job));
  }

  getMatchPercentageColor(percentage?: number): string {
    if (!percentage) return '#ccc';
    if (percentage >= 80) return '#4caf50';
    if (percentage >= 60) return '#2196f3';
    if (percentage >= 40) return '#ff9800';
    return '#f44336';
  }
}
