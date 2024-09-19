from setuptools import setup, find_packages

setup(
    name="strange_loop_agent",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "openai",
        "anthropic",
        "pyrsistent"
    ],
    entry_points={
        "console_scripts": [
            "strange_loop_agent=strange_loop_agent.agent:main",
        ],
    },
)
