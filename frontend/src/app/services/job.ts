import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class JobService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getJobs() {
    return this.http.get(`${this.apiUrl}/jobs`);
  }
}
