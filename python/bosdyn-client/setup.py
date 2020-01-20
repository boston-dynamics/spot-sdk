import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bosdyn-client",
    version="1.0.1",
    author="Boston Dynamics",
    author_email="dev@bostondynamics.com",
    description="Boston Dynamics API client code and interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.bostondynamics.com/",
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    package_data={'': ['*.pem']},
    install_requires=['bosdyn-api==1.0.1', 'bosdyn-core==1.0.1', 'grpcio'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Private :: Do Not Upload",
    ],
)
