import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css',
})
export class SearchComponent {
  locations: string = '';
  positionTitles: string = '';
  jobBoardSites: string = '';

  isSearching = false;
  searchStatus: string = '';
  searchMessage: string = '';
  searchError: string = '';

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  startSearch(): void {
    this.searchError = '';
    this.searchMessage = '';

    // Validate inputs
    if (!this.locations.trim() || !this.positionTitles.trim() || !this.jobBoardSites.trim()) {
      this.searchError = 'Please fill in all fields';
      return;
    }

    // Parse inputs
    const locationsList = this.locations
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l);
    const titlesList = this.positionTitles
      .split('\n')
      .map((t) => t.trim())
      .filter((t) => t);
    const sitesList = this.jobBoardSites
      .split('\n')
      .map((s) => s.trim())
      .filter((s) => s);

    if (locationsList.length === 0 || titlesList.length === 0 || sitesList.length === 0) {
      this.searchError = 'Each field must contain at least one value';
      return;
    }

    this.isSearching = true;
    this.searchStatus = 'Starting search...';

    // Call backend API to start search
    const payload = {
      locations: locationsList,
      titles: titlesList,
      sites: sitesList,
    };

    this.http.post(`${this.apiUrl}/search`, payload).subscribe({
      next: (response: any) => {
        this.isSearching = false;
        this.searchStatus = 'Search completed!';
        this.searchMessage = `Found ${response.total_results || 0} total results`;
        console.log('Search response:', response);
      },
      error: (err) => {
        this.isSearching = false;
        this.searchError = `Search failed: ${err.error?.detail || err.message}`;
        console.error('Search error:', err);
      },
    });
  }

  clearForm(): void {
    this.locations = '';
    this.positionTitles = '';
    this.jobBoardSites = '';
    this.searchError = '';
    this.searchMessage = '';
    this.searchStatus = '';
  }
}
