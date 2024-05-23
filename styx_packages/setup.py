from setuptools import setup, find_packages

setup(
    name="styx_packages",
    version="0.3.1",
    packages=find_packages(
        include=["styx_logger", "styx_logger.*", "data_connector", "data_connector.*"]
    ),
    description="Shared packages for Styx project",
    install_requires=[
        "sqlalchemy",  # Add other dependencies if necessary
        "psycopg2-binary",
    ],
)
