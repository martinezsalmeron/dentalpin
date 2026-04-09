# Module Documentation

This directory contains developer documentation for each DentalPin module.

## Available Modules

| Module | Description | Documentation |
|--------|-------------|---------------|
| **budget** | Treatment quotes with versioning, signatures, and PDF | [budget.md](./budget.md) |

## Module Documentation Structure

Each module documentation includes:

1. **Overview** - Module purpose and structure
2. **Data Models** - Database schema and relationships
3. **Workflow** - State machine and transitions (if applicable)
4. **Events** - Published and subscribed events
5. **Extension Points** - How future modules can integrate
6. **API Endpoints** - REST API reference
7. **Permissions** - RBAC configuration
8. **Frontend Components** - Vue components and composables
9. **Testing** - How to run tests
10. **Migration Guide** - Best practices for extending

## Creating Module Documentation

When adding a new module, create `{module_name}.md` following the structure above. Key sections:

- Document all published events so other modules can subscribe
- List extension points for future integrations
- Include API endpoint reference with permissions
- Describe frontend components and their usage
