from graphviz import Digraph
from roadmap import roadmap  # Import the roadmap dictionary from the roadmap.py file


def create_mind_map(roadmap):
    dot = Digraph(comment="N.E.X.U.S. Roadmap")
    for phase, details in roadmap.items():
        dot.node(
            phase,
            phase,
            shape="box",
            style="filled",
            color="lightblue" if details["status"] == "completed" else "white",
        )
        for subphase, subdetails in details.items():
            if isinstance(subdetails, dict) and subphase != "status":
                dot.node(
                    subphase,
                    subphase,
                    shape="ellipse",
                    style="filled",
                    color=(
                        "lightgreen" if subdetails["status"] == "completed" else "white"
                    ),
                )
                dot.edge(phase, subphase)
                for task in subdetails["tasks"]:
                    dot.node(task, task, shape="note", style="filled", color="yellow")
                    dot.edge(subphase, task)
    return dot


dot = create_mind_map(roadmap)
dot.render("output/roadmap", format="png", view=False)
