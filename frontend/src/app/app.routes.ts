import { Routes } from '@angular/router';
import { JobsListComponent } from './pages/jobs-list.component';

export const routes: Routes = [
  { path: '', redirectTo: '/jobs', pathMatch: 'full' },
  { path: 'jobs', component: JobsListComponent },
];
