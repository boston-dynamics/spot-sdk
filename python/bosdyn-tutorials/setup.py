import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bosdyn-tutorials",
    version="1.0.1",
    author="Boston Dynamics",
    author_email="dev@bostondynamics.com",
    description="Boston Dynamics API Core code and interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.bostondynamics.com/",
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    
    install_requires=[
    'bosdyn-api==1.0.1', 'bosdyn-client==1.0.1', 'Pillow>=6.0.0', 'matplotlib>=2.2.2'
    ],


    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Private :: Do Not Upload",
    ],
)
