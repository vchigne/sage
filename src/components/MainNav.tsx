```typescript
import Link from 'next/link';
import { Upload } from 'lucide-react';

export function MainNav() {
  return (
    <nav className="flex items-center space-x-4 lg:space-x-6">
      <Link
        href="/"
        className="text-sm font-medium transition-colors hover:text-primary"
      >
        Inicio
      </Link>
      <Link
        href="/upload"
        className="text-sm font-medium transition-colors hover:text-primary"
      >
        <div className="flex items-center space-x-2">
          <Upload className="h-4 w-4" />
          <span>Subir Archivos</span>
        </div>
      </Link>
    </nav>
  );
}
```
