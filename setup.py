from setuptools import setup, find_packages

requirements = ["cffi>=1.0.0"]
setup(
    name="avalanche",
    package_dir={"": "src"},
    description="Python integration for Avalanche performance measurement",
    version="0.1.0",
    author="Arthur Pastel",
    author_email="arthur.pastel@gmail.com",
    license="MIT",
    classifiers=[
        "Framework :: Pytest",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Benchmark",
        "Topic :: Utilities",
        "Typing :: Typed",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords=["pytest", "benchmark", "performance", "measurement", "avalanche"],
    packages=find_packages(
        "src/", exclude=["src/avalanche_pytest/_callgrind_wrapper.py"]
    ),
    python_requires=">=3.8",
    setup_requires=requirements,
    install_requires=requirements,
    ext_package="avalanche",
    cffi_modules=["src/avalanche_pytest/_callgrind_wrapper.py:ffi"],
    entry_points={"pytest11": ["avalanche = avalanche_pytest.plugin"]},
)
