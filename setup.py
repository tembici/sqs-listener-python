from setuptools import find_packages, setup  # type: ignore

setup(
    name="sqslistener",
    version="v0.1.2-beta",
    url="https://github.com/tembici/sqs-listener-python",
    description="",
    long_description="",
    author="Tembici",
    author_email="falecomagente@tembici.com.br",
    packages=find_packages(exclude=[]),
    include_package_data=True,
    install_requires=["boto3"],
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
