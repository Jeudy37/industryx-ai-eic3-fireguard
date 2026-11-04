from glob import glob

from setuptools import find_packages, setup

package_name = "industry_x_ai"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Équipe FIREGUARD-X",
    maintainer_email="fireguard-x@example.org",
    description="INDUSTRY-X AI : cellule de tri robotisée",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "conveyor_node = industry_x_ai.conveyor_node:main",
            "robot_a_node = industry_x_ai.robot_a_node:main",
            "robot_b_node = industry_x_ai.robot_b_node:main",
            "orchestrator_node = industry_x_ai.orchestrator_node:main",
            "perception_node = industry_x_ai.perception_node:main",
            "supervision_node = industry_x_ai.supervision_node:main",
            "headless_sim = industry_x_ai.headless_sim:main",
        ],
    },
)
