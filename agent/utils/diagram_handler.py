code = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

filename = "./output/diagram_image"
with Diagram("Grouped Workers", show=False, direction="TB", filename=filename):
    ELB("lb") >> [EC2("worker1"),
                  EC2("worker2"),
                  EC2("worker3"),
                  EC2("worker4"),
                  EC2("worker5")] >> RDS("events")
"""
def generate():
    exec(code)
