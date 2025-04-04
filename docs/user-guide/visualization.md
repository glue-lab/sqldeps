# Interactive Visualization of SQL Dependencies

SQLDeps provides powerful visualization capabilities to help you understand and explore SQL dependencies across your projects.

## Interactive Dependency Graphs

The `visualize_sql_dependencies()` function creates an interactive network graph that shows the relationships between SQL files, tables, and their dependencies.

### Basic Usage

```python
from sqldeps.llm_parsers import create_extractor
from sqldeps.visualization import visualize_sql_dependencies

# Create an interactive network graph from multiple SQL files
extractor = create_extractor()
sql_profiles = extractor.extract_from_folder("path/to/folder", recursive=False)

# Generate an interactive visualization (saving output to an HTML file)
figure = visualize_sql_dependencies(sql_profiles, output_path="dependencies.html")

# Show figure on IDE
figure.show()
```

### Visualization Options

The `visualize_sql_dependencies()` function offers extensive customization:

```python
# See API documentation for more options
# https://sqldeps.readthedocs.io/en/latest/api-reference/visualization

figure = visualize_sql_dependencies(
    dependencies,
    output_path="dependencies.html",  # Optional: Save to HTML file
    show_columns=True,                # Show column details in hover text
    layout_algorithm="spring",        # Layout options: 'spring', 'circular', 'kamada_kawai'
    highlight_common_tables=True,     # Highlight tables used by multiple files
    show_file_text=True,              # Show file names
    show_table_text=False,            # Show table names
    color_gradient=True,              # Color intensity based on usage frequency
    min_file_size=20,                 # Minimum node size for files
    max_file_size=40,                 # Maximum node size for files
    show_text_buttons=True,           # Add buttons to toggle text visibility
    show_layout_buttons=True          # Add buttons to change graph layout
)
```

### Visualization Features

- **Interactive Exploration**: Hover over nodes to see detailed information
- **Dynamic Layout**: Change graph layout with built-in buttons
- **Text Toggle**: Show/hide labels for files and tables
- **Usage Visualization**: 
    - Node sizes indicate usage frequency
    - Color intensity represents how many files use a particular table
- **Dependency Insights**: 
    - Visualize connections between SQL files and tables
    - Identify common tables across multiple files

### Example Use Cases

1. **Project Dependency Mapping**
```python
# Map dependencies across an entire project
project_deps = extractor.extract_from_folder(
    "path/to/project/sql", 
    recursive=True
)
# Plot dependencies
visualize_sql_dependencies(project_deps, output_path="project_deps.html")
```

2. **Focused Analysis**
```python
# Analyze dependencies for a specific subset of files
subset_deps = extractor.extract_from_folder(
    "path/to/specific/sql/folder", 
    recursive=False
)
# Plot dependencies
visualize_sql_dependencies(subset_deps, output_path="subset_deps.html")
```

## Use cases

You can use the visualization to identify:

  - Shared tables across different files
  - Potential refactoring opportunities
  - Complex dependency relationships

> Note: The visualization is best suited for projects with a moderate number of SQL files
