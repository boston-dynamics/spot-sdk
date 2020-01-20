import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bosdyn-core",
    version="0.0.1",
    author="Boston Dynamics",
    author_email="dev@bostondynamics.com",
    description="Boston Dynamics API Core code and interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://api.bostondynamics.com/",
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['bosdyn-api>=0.0.1'],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Private :: Do Not Upload",
    ],
)
