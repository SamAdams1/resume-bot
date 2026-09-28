import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface SearchConfig {
  locations: string;
  positionTitles: string;
  jobBoardSites: string;
  excludeKeywords: string;
  timestamp: number;
}

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css',
})
export class SearchComponent implements OnInit, OnDestroy {
  locations: string = '';
  positionTitles: string = '';
  jobBoardSites: string = '';
  excludeKeywords: string = '';

  isSearching = false;
  searchStatus: string = '';
  searchMessage: string = '';
  searchError: string = '';

  private apiUrl = 'http://localhost:8000';
  private storageKey = 'jobSearchConfig';
  private saveTimeout: any;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadSearchConfig();
  }

  ngOnDestroy(): void {
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
    }
    // Save to backend when component is destroyed
    this.saveSearchConfigToBackend();
  }

  private saveSearchConfigToBackend(): void {
    const config: SearchConfig = {
      locations: this.locations,
      positionTitles: this.positionTitles,
      jobBoardSites: this.jobBoardSites,
      excludeKeywords: this.excludeKeywords,
      timestamp: Date.now(),
    };

    this.http.post(`${this.apiUrl}/search-config/save`, config).subscribe({
      next: () => {
        console.log('Search config saved to backend');
      },
      error: (err) => {
        console.warn('Failed to save search config to backend:', err);
      },
    });
  }

  private saveSearchConfig(): void {
    const config: SearchConfig = {
      locations: this.locations,
      positionTitles: this.positionTitles,
      jobBoardSites: this.jobBoardSites,
      excludeKeywords: this.excludeKeywords,
      timestamp: Date.now(),
    };
    localStorage.setItem(this.storageKey, JSON.stringify(config));
    console.log('Search config saved to localStorage');
  }

  private loadSearchConfig(): void {
    // First try to load from backend
    this.http.get<any>(`${this.apiUrl}/search-config/load`).subscribe({
      next: (config) => {
        if (config) {
          this.locations = Array.isArray(config.locations)
            ? config.locations.join('\n')
            : config.locations || '';
          this.positionTitles = Array.isArray(config.positionTitles)
            ? config.positionTitles.join('\n')
            : config.positionTitles || '';
          this.jobBoardSites = Array.isArray(config.jobBoardSites)
            ? config.jobBoardSites.join('\n')
            : config.jobBoardSites || '';
          this.excludeKeywords = Array.isArray(config.excludeKeywords)
            ? config.excludeKeywords.join('\n')
            : config.excludeKeywords || '';
          console.log('Search config loaded from backend');
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        console.log('Backend config not available, trying localStorage');
        this.loadSearchConfigFromLocalStorage();
      },
    });
  }

  private loadSearchConfigFromLocalStorage(): void {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        const config: any = JSON.parse(saved);
        this.locations = Array.isArray(config.locations)
          ? config.locations.join('\n')
          : config.locations || '';
        this.positionTitles = Array.isArray(config.positionTitles)
          ? config.positionTitles.join('\n')
          : config.positionTitles || '';
        this.jobBoardSites = Array.isArray(config.jobBoardSites)
          ? config.jobBoardSites.join('\n')
          : config.jobBoardSites || '';
        this.excludeKeywords = Array.isArray(config.excludeKeywords)
          ? config.excludeKeywords.join('\n')
          : config.excludeKeywords || '';
        console.log('Search config loaded from localStorage');
        this.cdr.detectChanges();
      }
    } catch (error) {
      console.error('Failed to load search config from localStorage:', error);
    }
  }

  onConfigChange(): void {
    // Debounce the save to avoid too many requests while typing
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
    }
    this.saveTimeout = setTimeout(() => {
      this.saveSearchConfigToBackend();
    }, 500); // Save 500ms after the user stops typing
  }

  exportConfig(): void {
    const config: SearchConfig = {
      locations: this.locations,
      positionTitles: this.positionTitles,
      jobBoardSites: this.jobBoardSites,
      excludeKeywords: this.excludeKeywords,
      timestamp: Date.now(),
    };

    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `job-search-config-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  importConfig(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e: any) => {
      try {
        const config: any = JSON.parse(e.target.result);
        this.locations = Array.isArray(config.locations)
          ? config.locations.join('\n')
          : config.locations || '';
        this.positionTitles = Array.isArray(config.positionTitles)
          ? config.positionTitles.join('\n')
          : config.positionTitles || '';
        this.jobBoardSites = Array.isArray(config.jobBoardSites)
          ? config.jobBoardSites.join('\n')
          : config.jobBoardSites || '';
        this.excludeKeywords = Array.isArray(config.excludeKeywords)
          ? config.excludeKeywords.join('\n')
          : config.excludeKeywords || '';
        this.saveSearchConfig();
        this.searchMessage = 'Configuration imported successfully!';
        setTimeout(() => (this.searchMessage = ''), 3000);
      } catch (error) {
        this.searchError = 'Failed to import configuration: Invalid JSON file';
        console.error('Import error:', error);
      }
    };
    reader.readAsText(file);
  }

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

    // Parse exclude keywords (optional)
    const excludeList = this.excludeKeywords
      .split('\n')
      .map((e) => e.trim())
      .filter((e) => e);

    this.isSearching = true;
    this.searchStatus = 'Starting search...';

    // Call backend API to start search
    const payload: any = {
      locations: locationsList,
      titles: titlesList,
      sites: sitesList,
    };

    // Add exclude keywords if provided
    if (excludeList.length > 0) {
      payload.excludes = excludeList;
    }

    this.http.post(`${this.apiUrl}/search`, payload).subscribe({
      next: (response: any) => {
        this.isSearching = false;
        this.searchStatus = 'Search completed!';
        this.searchMessage = `Found ${response.total_results || 0} total results`;
        // Auto-save config after successful search
        this.saveSearchConfigToBackend();
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
    this.excludeKeywords = '';
    this.searchError = '';
    this.searchMessage = '';
    this.searchStatus = '';
    localStorage.removeItem(this.storageKey);
    // Also clear backend config
    this.http.post(`${this.apiUrl}/search-config/clear`, {}).subscribe({
      next: () => console.log('Backend config cleared'),
      error: (err) => console.warn('Failed to clear backend config:', err),
    });
  }
}
