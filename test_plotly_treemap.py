"""
Quick test script to verify Plotly treemap rendering
Run this to see if the issue is with Streamlit or the treemap data structure
"""

import plotly.graph_objects as go

# Create a simple test treemap
labels = ["Root", "A", "B", "C", "A1", "A2", "B1"]
parents = ["", "Root", "Root", "Root", "A", "A", "B"]
values = [10, 5, 3, 2, 2, 3, 3]
colors = ['#0ea5e9', '#10b981', '#a855f7', '#f59e0b', '#10b981', '#10b981', '#a855f7']

fig = go.Figure(go.Treemap(
    labels=labels,
    parents=parents,
    values=values,
    marker=dict(colors=colors, line=dict(width=2, color='#0b1121')),
    text=labels,
    textposition='middle center',
    branchvalues="total"
))

fig.update_layout(
    title="Simple Test Treemap",
    height=600,
    margin=dict(t=60, l=10, r=10, b=10)
)

# Save as HTML
fig.write_html("test_treemap.html")
print("✓ Treemap saved to test_treemap.html")
print("✓ Open this file in your browser to test if treemap rendering works")

# Also show the figure
fig.show()
