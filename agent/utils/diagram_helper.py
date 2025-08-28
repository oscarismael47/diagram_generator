import random
import textwrap
 
bgcolors = ["gray89"] # https://graphviz.gitlab.io/doc/info/colors.html

def check_modules(import_code):
    modules = import_code.split("\n")
    error_messages = []
    for module in modules:
        try:
            exec(module)
        except Exception as e:
            error_messages.append(str(e))
    if len(error_messages) == 0:
        return True, []
    else:
        return False, error_messages

def generate(import_code=None, diagram_code=None):
    # direction="TB",
    base_code = f"""
{import_code}
graph_attr = {{
    "bgcolor": "{random.choice(bgcolors)}",
    "margin":"-1.5, -2"
}}

filename = "diagram_image"
with Diagram("Diagram", show=True,  filename=filename, outformat="png", graph_attr=graph_attr):
{textwrap.indent(diagram_code, '    ')}
"""
    try:
        exec(base_code)
        error_message = None
    except Exception as e:
        error_message = str(e)
    return base_code, error_message

if __name__ == "__main__":
    
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
    response = generate(import_code=import_code_example, diagram_code=diagram_code_example)
    print(response)