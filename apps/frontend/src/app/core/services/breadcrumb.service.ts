import { Injectable, signal } from '@angular/core';
import { MenuItem } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})
export class BreadcrumbService {
  private breadcrumbItems = signal<MenuItem[]>([]);

  getBreadcrumbs() {
    return this.breadcrumbItems.asReadonly();
  }

  setBreadcrumbs(items: MenuItem[]) {
    this.breadcrumbItems.set(items);
  }

  clearBreadcrumbs() {
    this.breadcrumbItems.set([]);
  }

  // Helper method to generate breadcrumbs from route path
  generateFromPath(path: string, customLabels?: Record<string, string>) {
    const segments = path.split('/').filter(segment => segment);
    const items: MenuItem[] = [];

    // Add home as first item in the model
    items.push({ label: 'Αρχική', icon: 'pi pi-home', routerLink: '/app' });

    // Build breadcrumbs from segments
    let currentPath = '/app';
    
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      
      // Skip 'app' segment as it's already in home
      if (segment === 'app') continue;
      
      currentPath += `/${segment}`;
      
      // Use custom label if provided, otherwise format segment
      const label = customLabels?.[segment] || this.formatSegmentLabel(segment);
      
      // Don't add routerLink to the last item (current page)
      const isLast = i === segments.length - 1;
      
      items.push({
        label,
        routerLink: isLast ? undefined : currentPath
      });
    }

    this.setBreadcrumbs(items);
  }

  private formatSegmentLabel(segment: string): string {
    const labelMap: Record<string, string> = {
      'dashboard': 'Πίνακας Ελέγχου',
      'transcriptions': 'Μεταγραφές',
      'help': 'Βοήθεια',
      'faq': 'Συχνές Ερωτήσεις',
      'getting-started': 'Οδηγός Χρήσης',
      'api-docs': 'API Documentation',
      'about': 'Σχετικά με την Πλατφόρμα',
      'keyboard-shortcuts': 'Συντομεύσεις',
      'profile': 'Προφίλ',
      'analytics': 'Αναλυτικά',
      'users': 'Χρήστες',
      'settings': 'Ρυθμίσεις',
      'model-comparison': 'Σύγκριση Μοντέλων',
      'upload': 'Ανέβασμα',
      'create': 'Δημιουργία',
      'edit': 'Επεξεργασία'
    };

    return labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
  }
}