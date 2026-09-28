import { Routes } from '@angular/router';
import { JobsListComponent } from './pages/jobs-list.component';
import { SearchComponent } from './pages/search.component';

export const routes: Routes = [
  { path: '', redirectTo: '/jobs', pathMatch: 'full' },
  { path: 'jobs', component: JobsListComponent },
  { path: 'search', component: SearchComponent },
];
