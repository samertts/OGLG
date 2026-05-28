# Core Architecture Rules

- Each module MUST remain isolated and independently maintainable.
- Modules MUST communicate through clear service boundaries.
- Direct cross-module dependency is discouraged.
- Shared mutable global state is forbidden.
- Circular dependencies are forbidden.
- Core business logic MUST remain framework-independent.
- Infrastructure components MUST remain replaceable.
- UI logic MUST NOT contain business logic.
- Database logic MUST remain abstracted behind services/repositories.
- Future extensibility MUST NOT require full system redesign.
