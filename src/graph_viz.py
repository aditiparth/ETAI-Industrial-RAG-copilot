from pyvis.network import Network

DOC_TYPE_COLORS = {
    "regulatory": "#4C72B0",
    "maintenance": "#DD8452",
    "technical": "#55A868",
}
NODE_TYPE_COLORS = {
    "Equipment": "#C44E52",
    "Standard": "#8172B2",
}
REL_LABELS = {
    "MENTIONS": "mentions",
    "REFERENCES": "references",
}

def render_knowledge_graph(graph_data, height="650px", doc_type_filter=None):
    net = Network(height=height, width="100%", bgcolor="#0e1117", font_color="white", directed=True)

    # Better spacing — less clutter, slower settle, more spread out
    net.set_options("""
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.15,
          "springLength": 220,
          "springConstant": 0.03,
          "damping": 0.5,
          "avoidOverlap": 1
        },
        "minVelocity": 0.75,
        "stabilization": { "iterations": 250 }
      },
      "edges": {
        "font": { "size": 11, "color": "#cccccc", "strokeWidth": 0 },
        "color": { "color": "#555555", "highlight": "#ffffff" },
        "smooth": { "type": "continuous" },
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } },
        "width": 1
      },
      "nodes": {
        "font": { "size": 14, "face": "arial" },
        "borderWidth": 2
      }
    }
    """)

    added_docs = {}
    added_entities = {}
    edge_set = set()

    for row in graph_data:
        doc_source = row["doc_source"]
        doc_type = row["doc_type"]
        node_name = row["node_name"]
        node_type = row["node_type"]
        rel_type = row["rel_type"]

        if doc_type_filter and doc_type not in doc_type_filter:
            continue

        # add / grow document node
        if doc_source not in added_docs:
            net.add_node(
                doc_source,
                label=doc_source if len(doc_source) <= 22 else doc_source[:19] + "...",
                title=f"📄 {doc_source}\nType: {doc_type}",
                color=DOC_TYPE_COLORS.get(doc_type, "#888888"),
                shape="dot", size=18,
            )
            added_docs[doc_source] = 1
        else:
            added_docs[doc_source] += 1

        if not node_name:
            continue

        # add / grow entity node — size grows with how many docs reference it
        # (a hub node like a widely-referenced standard should look bigger)
        if node_name not in added_entities:
            net.add_node(
                node_name,
                label=node_name,
                title=f"{'⚙️' if node_type == 'Equipment' else '📘'} {node_type}: {node_name}",
                color=NODE_TYPE_COLORS.get(node_type, "#CCCCCC"),
                shape="diamond" if node_type == "Equipment" else "triangle",
                size=22,
            )
            added_entities[node_name] = 1
        else:
            added_entities[node_name] += 1
            # bump size slightly for hub nodes, capped
            net.get_node(node_name)["size"] = min(22 + added_entities[node_name] * 3, 45)

        edge_key = (doc_source, node_name, rel_type)
        if edge_key not in edge_set:
            net.add_edge(
                doc_source, node_name,
                label=REL_LABELS.get(rel_type, rel_type.lower()),
                title=f"{doc_source} → {rel_type} → {node_name}",
            )
            edge_set.add(edge_key)

    net.save_graph("knowledge_graph.html")
    with open("knowledge_graph.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html


def render_legend_html():
    return """
    <div style="display:flex; gap:24px; flex-wrap:wrap; padding:8px 4px; font-size:13px; color:#ccc;">
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#4C72B0;margin-right:6px;"></span>Regulatory Doc</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#DD8452;margin-right:6px;"></span>Maintenance Doc</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#55A868;margin-right:6px;"></span>Technical Doc</span>
      <span><span style="display:inline-block;width:12px;height:12px;background:#C44E52;margin-right:6px;transform:rotate(45deg);"></span>Equipment</span>
      <span><span style="display:inline-block;width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:12px solid #8172B2;margin-right:6px;"></span>Standard</span>
    </div>
    """