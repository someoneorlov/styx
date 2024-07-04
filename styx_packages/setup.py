from setuptools import setup, find_packages

setup(
    name="styx_packages",
    version="0.5.4",
    packages=find_packages(
        include=["styx_logger", "styx_logger.*", "data_connector", "data_connector.*"]
    ),
    description="Shared packages for Styx project",
    install_requires=[
        "sqlalchemy==2.0.25",  # Add other dependencies if necessary
        "psycopg2-binary==2.9.9",
    ],
)
