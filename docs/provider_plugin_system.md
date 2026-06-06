# Provider Plugin System

Assumptions:
- Providers live under scanner/providers and subclass ProviderScanner.

Boundaries:
- Providers must emit the shared ScanManifest shape.

Integration notes:
- New providers are auto-discovered through the registry.

Required interface:
class ProviderScanner:
    def detect(self, target: str | None = None) -> bool
    def scan(self, target: str | None = None) -> ScanManifest

Add a provider:
1. Create scanner/providers/<name>.py
2. Subclass ProviderScanner
3. Implement detect and scan
4. The registry will auto-discover it
