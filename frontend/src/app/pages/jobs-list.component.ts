import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Job, ExcludedJob } from '../models/job.model';

@Component({
  selector: 'app-jobs-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './jobs-list.component.html',
  styleUrl: './jobs-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobsListComponent implements OnInit {
  jobs: Job[] = [];
  excludedJobs: ExcludedJob[] = [];
  excludedJobUrls: Set<string> = new Set();
  loading = true;
  error: string | null = null;

  private apiUrl = 'http://localhost:8000';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
  ) {
    console.log('JobsListComponent initialized');
  }

  ngOnInit(): void {
    console.log('JobsListComponent ngOnInit called');
    this.fetchJobs();
    this.fetchExcludedJobs();
  }

  private fetchJobs(): void {
    console.log('Fetching jobs from:', `${this.apiUrl}/jobs`);
    this.http.get<any>(`${this.apiUrl}/jobs`).subscribe({
      next: (data) => {
        console.log('Jobs loaded successfully:', data);
        // Handle both array and object responses
        this.jobs = Array.isArray(data) ? data : [];
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error('Failed to load jobs:', err);
        this.error = `Failed to load jobs: ${err.message}`;
        this.loading = false;
        this.jobs = [];
        this.cdr.markForCheck();
      },
    });
  }

  private fetchExcludedJobs(): void {
    console.log('Fetching excluded jobs from:', `${this.apiUrl}/excludedJobs`);
    this.http.get<any>(`${this.apiUrl}/excludedJobs`).subscribe({
      next: (data) => {
        console.log('Excluded jobs loaded successfully:', data);
        // Handle both array and object responses
        this.excludedJobs = Array.isArray(data) ? data : [];
        // Safely map URLs, filtering out any without a URL
        this.excludedJobUrls = new Set(
          this.excludedJobs.filter((job) => job?.url).map((job) => job.url),
        );
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.warn('Failed to load excluded jobs (table may not exist):', err);
        // Gracefully handle missing table by setting empty arrays
        this.excludedJobs = [];
        this.excludedJobUrls = new Set();
        this.cdr.markForCheck();
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
