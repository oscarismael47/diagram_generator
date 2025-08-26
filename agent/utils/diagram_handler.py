import random
import textwrap
 
bgcolors = ["gray89"] # https://graphviz.gitlab.io/doc/info/colors.html
import_code_example = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
"""
diagram_code_example = """
ELB("lb") >> [EC2("worker1"),
    EC2("worker2"),
    EC2("worker3"),
    EC2("worker4"),
    EC2("worker5")] >> RDS("events")
"""

def generate(import_code=None, diagram_code=None):
    if import_code is None:
        import_code = import_code_example

    if diagram_code is None:
        diagram_code = diagram_code_example

    # direction="TB",
    base_code = f"""
{import_code}
graph_attr = {{
    "bgcolor": "{random.choice(bgcolors)}",
    "margin":"-1.5, -2"
}}

filename = "./output/diagram_image"
with Diagram("Diagram", show=False,  filename=filename, graph_attr=graph_attr):
{textwrap.indent(diagram_code, '    ')}
"""
    exec(base_code)
    return base_code