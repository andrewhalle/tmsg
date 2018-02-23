from setuptools import setup, find_packages

setup(
    name="tmsg",
    version="0.1",
    packages=find_packages(),
    install_requires=["fbchat==1.3.2"],
    author="Andrew Halle",
    author_email="ahalle@berkeley.edu",
    description="A curses based client for Facebook Messenger",
    license="MIT",
    url="https://github.com/andrewhalle/tmsg",
    entry_points={
        "console_scripts": [
            "tmsg = tmsg.tmsg:start_cli"
        ]
    }
)

