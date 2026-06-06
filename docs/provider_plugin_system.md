# Provider Plugin System

Assumptions:
- Providers live under scanner/providers and subclass ProviderScanner.
- Additional providers may be loaded from environment-configured module paths or Python entry points.

Boundaries:
- Providers must emit the shared ScanManifest shape.
- Providers do not bypass source tracking or governance rules.

Discovery paths:
1. Drop a provider file into scanner/providers/
2. Add a module path to SSOT_SCANNER_PROVIDER_MODULES
3. Register an entry point in group ssot_indexer.scanner_providers

Provider metadata:
- name
- version
- capabilities
- description

Required interface:
class ProviderScanner:
        provider_name: str
        version: str
        capabilities: tuple[str, ...]
        description: str
        def detect(self, target: str | None = None) -> bool
        def scan(self, target: str | None = None) -> ScanManifest

ASCII registry flow:
provider registry
    -> package discovery
    -> env module discovery
    -> entry-point discovery
    -> provider metadata
    -> provider instance

CLI surfaces:
- ssotctl providers list
- ssotctl providers info <name>

Integration notes:
- Warp can register future providers like Box, S3, or Synology Drive without changing core scanner routing.
