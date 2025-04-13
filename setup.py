from setuptools import setup, find_packages
from setuptools.command.install import install
from subprocess import Popen
import sys

major = sys.version_info.major
minor = sys.version_info.minor
micro = sys.version_info.micro

## We only support Python 3.12.2 for now
if major != 3 or minor != 12 or micro != 2:
    print("Python 3.12.2 is required to install this package, got {}.{}.{}".format(major, minor, micro))
    sys.exit(1)


def read_requirements():
    with open("requirements.txt") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


class PostInstallCommand(install):
    def run(self):
        install.run(self)
        command = "cd frontend && npm install --force && cd .."
        p = Popen(command, shell=True)
        p.wait()
        if p.returncode != 0:
            print("Error installing npm dependencies", file=sys.stderr)
            sys.exit(1)


setup(
    name="FlashCards",
    version="0.0.1",
    packages=find_packages(),
    install_requires=read_requirements(),
    cmdclass={
        "install": PostInstallCommand,
    },
    author="none",
    description="none",
)
