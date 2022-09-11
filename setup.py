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
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Benchmark",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    packages=find_packages(
        "src/", exclude=["src/avalanche_pytest/_callgrind_wrapper.py"]
    ),
    setup_requires=requirements,
    install_requires=requirements,
    ext_package="avalanche",
    cffi_modules=["src/avalanche_pytest/_callgrind_wrapper.py:ffi"],
    entry_points={"pytest11": ["avalanche = avalanche_pytest.plugin"]},
)
