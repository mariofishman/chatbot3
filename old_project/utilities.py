# function that takes a graph a saves to file a mermaid image
def save_graph(graph, path, xray=False):
    png_bytes = graph.get_graph(xray=xray).draw_mermaid_png()

    with open(path, "wb") as f:
        f.write(png_bytes)
