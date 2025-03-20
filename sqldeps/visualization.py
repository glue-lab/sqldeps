import os
from typing import Any

import networkx as nx
import plotly.colors as pcolors
import plotly.graph_objects as go


def visualize_sql_dependencies(  # noqa: C901
    dependencies: dict[str, dict[str, Any]],
    output_path: str | None = None,
    show_columns: bool = True,
    layout_algorithm: str = "spring",
    min_file_size: int = 20,
    max_file_size: int = 40,
    min_table_size: int = 15,
    max_table_size: int = 30,
    highlight_common_tables: bool = True,
    file_symbol: str = "hexagon2",
    table_symbol: str = "circle",
    color_gradient: bool = False,
    file_colorscale=None,
    table_colorscale=None,
    common_table_colorscale=None,
    show_file_text: bool = True,
    show_table_text: bool = False,
    text_font_size: int = 10,
    show_text_buttons: bool = False,
    show_layout_buttons: bool = False,
) -> go.Figure:
    """
    Create an interactive graph visualization of SQL file dependencies.

    Args:
        dependencies: Dictionary where keys are filenames and values are
                      dependency objects with 'tables' and 'columns' attributes
        output_path: Optional path to save the HTML output
        show_columns: Whether to include column details in hover text
        layout_algorithm: Graph layout algorithm ('spring', 'circular', 'kamada_kawai')
        min_file_size, max_file_size: Size range for file nodes
        min_table_size, max_table_size: Size range for table nodes
        highlight_common_tables: Whether to highlight tables used by multiple files
        file_symbol: Symbol to use for file nodes ("circle", "square", etc.)
        table_symbol: Symbol to use for table nodes
        color_gradient: Whether to use color gradient based on usage frequency
        file_colorscale: Custom colorscale for files (default: Blues)
        table_colorscale: Custom colorscale for tables (default: Oranges)
        common_table_colorscale: Custom colorscale for common tables (default: Reds)
        show_file_text: Whether to display text labels for file nodes
        show_table_text: Whether to display text labels for table nodes
        text_font_size: Font size for node text labels
        show_text_buttons: Whether to display buttons for toggling text visibility
        show_layout_buttons: Whether to display buttons for changing the graph layout

    Returns:
        Plotly figure object
    """
    # Create a graph
    G = nx.Graph()  # noqa: N806 # lib convention

    # Track which tables are used by which files
    table_usage: dict[str, list[str]] = {}
    table_columns: dict[str, set[str]] = {}

    # Store all nodes and edges for layout recalculation
    node_data = {}
    edges = []

    # Set default colorscales if not provided
    if file_colorscale is None:
        file_colorscale = pcolors.sequential.Blues
    if table_colorscale is None:
        table_colorscale = pcolors.sequential.Oranges
    if common_table_colorscale is None:
        common_table_colorscale = pcolors.sequential.Reds

    # Add nodes and edges
    for filename, deps in dependencies.items():
        # Use just the base filename for display
        base_filename = os.path.basename(filename)

        # Add file node if it doesn't exist
        if base_filename not in G.nodes:
            G.add_node(base_filename, type="file", full_path=filename)
            node_data[base_filename] = {"type": "file", "full_path": filename}

        # Process tables
        for table in deps.get("tables", []):
            # Track table usage
            if table not in table_usage:
                table_usage[table] = []
            table_usage[table].append(base_filename)

            # Add table node if it doesn't exist
            if table not in G.nodes:
                G.add_node(table, type="table")
                node_data[table] = {"type": "table"}

            # Add edge from file to table
            G.add_edge(base_filename, table)
            edges.append((base_filename, table))

            # Track columns for this table
            if show_columns and table in deps.get("columns", {}):
                if table not in table_columns:
                    table_columns[table] = set()
                table_columns[table].update(deps["columns"][table])

    # Function to calculate layout for different algorithms
    def get_layout(algorithm):
        if algorithm == "spring":
            return nx.spring_layout(G, k=0.2, iterations=50)
        elif algorithm == "circular":
            return nx.circular_layout(G)
        elif algorithm == "kamada_kawai":
            return nx.kamada_kawai_layout(G)
        elif algorithm == "shell":
            # Create shells: files outer, tables inner
            shells = [
                [n for n in G.nodes() if G.nodes[n].get("type") == "file"],
                [n for n in G.nodes() if G.nodes[n].get("type") == "table"],
            ]
            return nx.shell_layout(G, shells)
        else:  # random
            return nx.random_layout(G)

    # Calculate initial layout
    pos = get_layout(layout_algorithm)

    # Store node positions as a JSON-serializable object for layout buttons
    layout_data = {}
    for node, position in pos.items():
        layout_data[node] = {"x": float(position[0]), "y": float(position[1])}

    # Create separate traces for each node type to allow toggling via legend
    file_nodes = {}
    regular_table_nodes = {}
    common_table_nodes = {}

    # Identify common tables (used by multiple files)
    common_tables = {table for table, files in table_usage.items() if len(files) > 1}

    # Get max usage count for scaling
    max_usage_count = max([len(files) for files in table_usage.values()], default=1)

    # Prepare edge data
    edge_x = []
    edge_y = []

    # Process edges first
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Process nodes and organize them by type
    for node in G.nodes():
        x, y = pos[node]
        node_type = G.nodes[node].get("type")

        if node_type == "file":
            # File nodes
            full_path = G.nodes[node].get("full_path", node)
            connected_tables = [n for n in G.neighbors(node)]
            hover_text = f"<b>File:</b> {full_path}<br>"
            hover_text += f"<b>Tables Used:</b> {len(connected_tables)}<br>"
            hover_text += "<br>".join(f"- {table}" for table in connected_tables)

            # Size based on number of connected tables
            # Scale between min_file_size and max_file_size
            table_count = len(connected_tables)
            max_tables = max(
                [
                    len([n for n in G.neighbors(node)])
                    for node in G.nodes()
                    if G.nodes[node].get("type") == "file"
                ],
                default=1,
            )
            size = min_file_size + (max_file_size - min_file_size) * (
                table_count / max(max_tables, 1)
            )

            # Calculate color based on relative complexity (table count)
            if color_gradient:
                color_intensity = table_count / max(max_tables, 1)
                file_color = pcolors.sample_colorscale(
                    file_colorscale, [color_intensity]
                )[0]
            else:
                file_color = "rgba(31, 119, 180, 0.8)"

            file_nodes[node] = {
                "x": x,
                "y": y,
                "text": node,
                "hover_text": hover_text,
                "size": size,
                "color": file_color,
            }
        else:
            # Table nodes
            is_common = node in common_tables
            usage_count = len(table_usage.get(node, []))

            hover_text = f"<b>Table:</b> {node}<br>"
            hover_text += (
                f"<b>Used by {usage_count} file"
                f"{'s' if usage_count != 1 else ''}:</b><br>"
            )
            hover_text += "<br>".join(f"- {f}" for f in table_usage.get(node, []))

            if show_columns and node in table_columns:
                columns_list = sorted(table_columns[node])
                hover_text += f"<br><br><b>Columns ({len(columns_list)}):</b><br>"
                hover_text += "<br>".join(f"- {col}" for col in columns_list)

            # Scale between min_table_size and max_table_size based on usage count
            size = min_table_size + (max_table_size - min_table_size) * (
                usage_count / max(max_usage_count, 1)
            )

            # Calculate color intensity based on usage count if gradient is enabled
            if color_gradient:
                color_intensity = usage_count / max(max_usage_count, 1)

                if is_common and highlight_common_tables:
                    table_color = pcolors.sample_colorscale(
                        common_table_colorscale, [color_intensity]
                    )[0]
                else:
                    table_color = pcolors.sample_colorscale(
                        table_colorscale, [color_intensity]
                    )[0]
            else:
                table_color = (
                    "rgba(214, 39, 40, 0.8)"
                    if is_common and highlight_common_tables
                    else "rgba(255, 127, 14, 0.8)"
                )

            if is_common and highlight_common_tables:
                common_table_nodes[node] = {
                    "x": x,
                    "y": y,
                    "text": node,
                    "hover_text": hover_text,
                    "size": size,
                    "color": table_color,
                }
            else:
                regular_table_nodes[node] = {
                    "x": x,
                    "y": y,
                    "text": node,
                    "hover_text": hover_text,
                    "size": size,
                    "color": table_color,
                }

    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="rgba(150, 150, 150, 0.5)"),
        hoverinfo="none",
        mode="lines",
        showlegend=False,
    )

    # Create traces for each node type with appropriate legends
    traces = []

    # Add edge trace first (bottom layer)
    traces.append(edge_trace)

    # Create SQL file trace - determine mode based on whether to show text
    file_mode = "markers+text" if show_file_text else "markers"

    # Create SQL file trace
    if file_nodes:
        file_trace = go.Scatter(
            x=[data["x"] for data in file_nodes.values()],
            y=[data["y"] for data in file_nodes.values()],
            mode=file_mode,
            name="SQL File",
            text=[data["text"] for data in file_nodes.values()],
            textposition="top center",
            hovertext=[data["hover_text"] for data in file_nodes.values()],
            hoverinfo="text",
            marker=dict(
                symbol=file_symbol,
                size=[data["size"] for data in file_nodes.values()],
                color=[data["color"] for data in file_nodes.values()]
                if color_gradient
                else "rgba(31, 119, 180, 0.8)",
                line=dict(width=1, color="rgba(31, 119, 180, 1)"),
            ),
            textfont=dict(size=text_font_size),
        )
        traces.append(file_trace)

    # Table mode based on show_table_text parameter
    table_mode = "markers+text" if show_table_text else "markers"

    # Create regular table trace
    if regular_table_nodes:
        regular_table_trace = go.Scatter(
            x=[data["x"] for data in regular_table_nodes.values()],
            y=[data["y"] for data in regular_table_nodes.values()],
            mode=table_mode,
            name="Table",
            text=[data["text"] for data in regular_table_nodes.values()],
            textposition="top center",
            hovertext=[data["hover_text"] for data in regular_table_nodes.values()],
            hoverinfo="text",
            marker=dict(
                symbol=table_symbol,
                size=[data["size"] for data in regular_table_nodes.values()],
                color=[data["color"] for data in regular_table_nodes.values()]
                if color_gradient
                else "rgba(255, 127, 14, 0.8)",
                line=dict(width=1, color="rgba(255, 127, 14, 1)"),
            ),
            textfont=dict(size=text_font_size),
        )
        traces.append(regular_table_trace)

    # Create common table trace
    if common_table_nodes and highlight_common_tables:
        common_table_trace = go.Scatter(
            x=[data["x"] for data in common_table_nodes.values()],
            y=[data["y"] for data in common_table_nodes.values()],
            mode=table_mode,
            name="Common Table",
            text=[data["text"] for data in common_table_nodes.values()],
            textposition="top center",
            hovertext=[data["hover_text"] for data in common_table_nodes.values()],
            hoverinfo="text",
            marker=dict(
                symbol=table_symbol,
                size=[data["size"] for data in common_table_nodes.values()],
                color=[data["color"] for data in common_table_nodes.values()]
                if color_gradient
                else "rgba(214, 39, 40, 0.8)",
                line=dict(width=2, color="rgba(214, 39, 40, 1)"),
            ),
            textfont=dict(size=text_font_size),
        )
        traces.append(common_table_trace)

    # Create figure with all traces
    fig = go.Figure(data=traces)

    # Initialize updatemenus
    updatemenus = []

    # Add text toggle buttons if requested
    if show_text_buttons:
        text_buttons = dict(
            type="buttons",
            direction="right",
            buttons=[
                dict(
                    args=[
                        {
                            "mode": [
                                "lines",
                                "markers+text",
                                "markers+text",
                                "markers+text",
                            ]
                            if len(traces) == 4
                            else ["lines", "markers+text", "markers+text"]
                        }
                    ],
                    label="Show All Text",
                    method="restyle",
                ),
                dict(
                    args=[
                        {
                            "mode": ["lines", "markers", "markers", "markers"]
                            if len(traces) == 4
                            else ["lines", "markers", "markers"]
                        }
                    ],
                    label="Hide All Text",
                    method="restyle",
                ),
                dict(
                    args=[
                        {
                            "mode": ["lines", "markers+text", "markers", "markers"]
                            if len(traces) == 4
                            else ["lines", "markers+text", "markers"]
                        }
                    ],
                    label="Files Text Only",
                    method="restyle",
                ),
                dict(
                    args=[
                        {
                            "mode": ["lines", "markers", "markers+text", "markers+text"]
                            if len(traces) == 4
                            else ["lines", "markers", "markers+text"]
                        }
                    ],
                    label="Tables Text Only",
                    method="restyle",
                ),
            ],
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.5,
            xanchor="center",
            y=1.15,
            yanchor="top",
        )
        updatemenus.append(text_buttons)

    # Add layout change buttons if requested
    if show_layout_buttons:
        # Generate different layouts
        layouts = {
            "spring": get_layout("spring"),
            "kamada_kawai": get_layout("kamada_kawai"),
            "circular": get_layout("circular"),
            "shell": get_layout("shell"),
        }

        # Create buttons for each layout
        layout_buttons = []
        for layout_name, layout_pos in layouts.items():
            # Edges first
            edge_x = []
            edge_y = []
            for edge in edges:
                source, target = edge
                x0, y0 = layout_pos[source]
                x1, y1 = layout_pos[target]
                edge_x.extend([float(x0), float(x1), None])
                edge_y.extend([float(y0), float(y1), None])

            # File nodes
            file_x = [float(layout_pos[node][0]) for node in file_nodes]
            file_y = [float(layout_pos[node][1]) for node in file_nodes]

            # Table nodes
            regular_table_x = [
                float(layout_pos[node][0]) for node in regular_table_nodes
            ]
            regular_table_y = [
                float(layout_pos[node][1]) for node in regular_table_nodes
            ]

            # Common table nodes if present
            common_table_x = []
            common_table_y = []
            if common_table_nodes:
                common_table_x = [
                    float(layout_pos[node][0]) for node in common_table_nodes
                ]
                common_table_y = [
                    float(layout_pos[node][1]) for node in common_table_nodes
                ]

            # Create button args for this layout
            if len(traces) == 4:  # With common tables
                args = [
                    {
                        "x": [edge_x, file_x, regular_table_x, common_table_x],
                        "y": [edge_y, file_y, regular_table_y, common_table_y],
                    }
                ]
            else:  # Without common tables
                args = [
                    {
                        "x": [edge_x, file_x, regular_table_x],
                        "y": [edge_y, file_y, regular_table_y],
                    }
                ]

            # Create button
            button = dict(args=args, label=layout_name.capitalize(), method="update")
            layout_buttons.append(button)

        # Add layout button menu
        layout_menu = dict(
            type="buttons",
            direction="right",
            buttons=layout_buttons,
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.5,
            xanchor="center",
            y=1.08 if show_text_buttons else 1.15,
            yanchor="top",
        )
        updatemenus.append(layout_menu)

    # Set top margin based on buttons
    top_margin = 40
    if show_text_buttons and show_layout_buttons:
        top_margin = 80
    elif show_text_buttons or show_layout_buttons:
        top_margin = 60

    # Update layout
    fig.update_layout(
        title=(
            f"SQL Dependency Graph ({len(dependencies)} files, "
            f"{len(table_usage)} tables)"
        ),
        title_font=dict(size=16),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, itemsizing="constant"
        ),
        updatemenus=updatemenus if updatemenus else None,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=top_margin),
        annotations=[
            dict(
                showarrow=False,
                text="Size indicates usage frequency",
                xref="paper",
                yref="paper",
                x=0.01,
                y=0.01,
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(248, 248, 248, 1)",
        paper_bgcolor="rgba(248, 248, 248, 1)",
    )

    # Save to HTML if output path provided
    if output_path:
        fig.write_html(output_path)

    return fig
