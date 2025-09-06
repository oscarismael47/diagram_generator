import random
import re
from datetime import datetime
 
bgcolors = ["gray89"] # https://graphviz.gitlab.io/doc/info/colors.html

def check_modules(import_code):
    modules = import_code.split("\n")
    error_messages = []
    for module in modules:
        try:
            exec(module)
        except Exception as e:
            error = str(e)
            error = re.sub(r"\(.*?\)", "", error).strip()
            error_messages.append(error)
    if len(error_messages) == 0:
        status = True
    else:
        status = False
    return status, error_messages

def generate(import_code=None, body_code=None):
    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename_value = f"\"./out/diagram_image_{now}\""
    base_code = f"""
{import_code}
graph_attr_value = {{
    "bgcolor": "{random.choice(bgcolors)}",
    "margin":"-1.5, -2"
}}

filename_value = {filename_value}
{body_code}
"""
    # {textwrap.indent(body_code, '    ')}
    try:
        exec(base_code)
        error_message = None
        image_path = f"{filename_value.strip('\"')}.png"
    except Exception as e:
        error_message = str(e)
        image_path = None
    return base_code, error_message, image_path

if __name__ == "__main__":
    
    import_code_example = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
"""

    body_code_example = """
ELB("lb") >> [EC2("worker1"),
    EC2("worker2"),
    EC2("worker3"),
    EC2("worker4"),
    EC2("worker5")] >> RDS("events")
"""
    response = generate(import_code=import_code_example, body_code=body_code_example)
    print(response)