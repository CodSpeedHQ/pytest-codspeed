# Changelog


<sub>The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).</sub>



## [3.2.0] - 2025-01-31

### <!-- 0 -->🚀 Features
- Increase the min round time to a bigger value (+/- 1ms) by @art049
- Add benchmarks-walltime job to run additional performance benchmarks by @art049 in [#65](https://github.com/CodSpeedHQ/pytest-codspeed/pull/65)
- Fix the random seed while measuring with instruments by @art049 in [#48](https://github.com/CodSpeedHQ/pytest-codspeed/pull/48)

### <!-- 1 -->🐛 Bug Fixes
- Use time per iteration instead of total round time in stats by @art049

### <!-- 2 -->🏗️ Refactor
- Replace hardcoded outlier factor for improved readability by @art049 in [#67](https://github.com/CodSpeedHQ/pytest-codspeed/pull/67)

### <!-- 7 -->⚙️ Internals
- Fix self-dependency by @adriencaccia in [#66](https://github.com/CodSpeedHQ/pytest-codspeed/pull/66)
- Fix uv version in CI by @adriencaccia


## [3.1.2] - 2025-01-09

### <!-- 1 -->🐛 Bug Fixes
- Update package_data to include header and source files for valgrind wrapper by @art049 in [#64](https://github.com/CodSpeedHQ/pytest-codspeed/pull/64)


## [3.1.1] - 2025-01-07

### <!-- 7 -->⚙️ Internals
- Fix tag num with bumpver by @art049 in [#61](https://github.com/CodSpeedHQ/pytest-codspeed/pull/61)
- Update uv lock before release by @art049
- Add a py3-none-any fallback wheel by @art049


## [3.1.0] - 2024-12-09

### <!-- 2 -->🏗️ Refactor
- Remove the scripted semver generation by @art049

### <!-- 7 -->⚙️ Internals
- Fix typo in cibuildwheel config by @art049 in [#57](https://github.com/CodSpeedHQ/pytest-codspeed/pull/57)


## [3.1.0-beta] - 2024-12-06

### <!-- 0 -->🚀 Features
- Check buildability and fallback when build doesn't work by @art049
- Compile the callgrind wrapper at build time by @art049

### <!-- 1 -->🐛 Bug Fixes
- Allow build on arm64 by @art049

### <!-- 7 -->⚙️ Internals
- Build wheels with cibuildwheel by @art049
- Allow forcing integrated tests by @art049
- Fix release script by @art049
- Use bumpver to manage versions by @art049
- Add a changelog by @art049
- Force native extension build in CI by @art049
- Updated matrix release workflow by @art049
- Use a common python version in the codspeed job by @art049
- Fix the codspeed workflow by @art049
- Use uv in CI by @art049
- Commit uv lock file by @art049


## [3.0.0] - 2024-10-29

### <!-- 1 -->🐛 Bug Fixes
- Fix compatibility with pytest-benchmark 5.0.0 by @art049 in [#54](https://github.com/CodSpeedHQ/pytest-codspeed/pull/54)

### <!-- 7 -->⚙️ Internals
- Drop support for python3.8 by @art049
- Expose type information (#53) by @Dreamsorcerer in [#53](https://github.com/CodSpeedHQ/pytest-codspeed/pull/53)
- Run the CI with ubuntu 24.04 by @art049
- Improve naming in workflow examples by @art049
- Bump actions/checkout to v4 (#47) by @fargito in [#47](https://github.com/CodSpeedHQ/pytest-codspeed/pull/47)


## [3.0.0b4] - 2024-09-27

### <!-- 0 -->🚀 Features
- Send more outlier data by @art049

### <!-- 1 -->🐛 Bug Fixes
- Fix display of parametrized tests by @art049
- Reenable gc logic by @art049

### <!-- 6 -->🧪 Testing
- Add benches for various syscalls by @art049


## [3.0.0b3] - 2024-09-26

### <!-- 0 -->🚀 Features
- Also save the lower and upper fences in the json data by @art049 in [#46](https://github.com/CodSpeedHQ/pytest-codspeed/pull/46)

### <!-- 6 -->🧪 Testing
- Refactor the algorithm benches using parametrization and add benches on bit_manipulation by @art049


## [3.0.0b2] - 2024-09-24

### <!-- 0 -->🚀 Features
- Also save the q1 and q3 in the json data by @art049 in [#45](https://github.com/CodSpeedHQ/pytest-codspeed/pull/45)
- Add the --codspeed-max-time flag by @art049


## [3.0.0b1] - 2024-09-20

### <!-- 0 -->🚀 Features
- Send the semver version to cospeed instead of the PEP440 one by @art049 in [#44](https://github.com/CodSpeedHQ/pytest-codspeed/pull/44)
- Also store the semver version by @art049

### <!-- 6 -->🧪 Testing
- Add benches for TheAlgorithms/backtracking by @art049 in [#43](https://github.com/CodSpeedHQ/pytest-codspeed/pull/43)


## [3.0.0b0] - 2024-09-18

### <!-- 0 -->🚀 Features
- Improve table style when displaying results by @art049 in [#41](https://github.com/CodSpeedHQ/pytest-codspeed/pull/41)
- Add the total bench time to the collected stats by @art049
- Add configuration and split tests between instruments by @art049
- Add outlier detection in the walltime instrument by @art049
- Implement the walltime instrument by @art049
- Add bench of various python noop by @art049
- Avoid overriding pytest's default protocol (#32) by @kenodegard in [#32](https://github.com/CodSpeedHQ/pytest-codspeed/pull/32)

### <!-- 1 -->🐛 Bug Fixes
- Use importlib_metadata to keep backward compatibility by @art049
- Properly decide the mode depending on our env variable spec by @art049
- Disable pytest-speed when installed and codspeed is enabled by @art049

### <!-- 2 -->🏗️ Refactor
- Differentiate the mode from the underlying instrument by @art049
- Move the instrumentation wrapper directly in the instrument by @art049
- Change Instrumentation to CPUInstrumentation by @art049
- Create an abstraction for each instrument by @art049

### <!-- 3 -->📚 Documentation
- Update action version in the CI workflow configuration (#39) by @frgfm in [#39](https://github.com/CodSpeedHQ/pytest-codspeed/pull/39)
- Bump action versions in README by @adriencaccia

### <!-- 6 -->🧪 Testing
- Add benches for TheAlgorithms/audio_filters by @art049 in [#42](https://github.com/CodSpeedHQ/pytest-codspeed/pull/42)

### <!-- 7 -->⚙️ Internals
- Add a test on the walltime instrument by @art049
- Fix utils test using a fake git repo by @art049
- Update readme by @art049
- Support python 3.13 and drop 3.7 by @art049 in [#40](https://github.com/CodSpeedHQ/pytest-codspeed/pull/40)
- Add TCH, FA, and UP to ruff lints (#29) by @kenodegard in [#29](https://github.com/CodSpeedHQ/pytest-codspeed/pull/29)


## [2.2.1] - 2024-03-19

### <!-- 0 -->🚀 Features
- Support pytest 8.1.1 by @art049

### <!-- 1 -->🐛 Bug Fixes
- Loosen runtime requirements (#21) by @edgarrmondragon in [#21](https://github.com/CodSpeedHQ/pytest-codspeed/pull/21)

### <!-- 7 -->⚙️ Internals
- Add all-checks job to CI workflow by @art049 in [#28](https://github.com/CodSpeedHQ/pytest-codspeed/pull/28)
- Switch from black to ruff format by @art049
- Update action version in README.md by @adriencaccia
- Add codspeed badge to the readme by @art049


## [2.2.0] - 2023-09-01

### <!-- 0 -->🚀 Features
- Avoid concurrent wrapper builds by @art049
- Add a test for pytest-xdist compatibility by @art049

### <!-- 1 -->🐛 Bug Fixes
- Fix xdist test output assertion by @art049


## [2.1.0] - 2023-07-27

### <!-- 1 -->🐛 Bug Fixes
- Fix relative git path when using working-directory by @art049 in [#15](https://github.com/CodSpeedHQ/pytest-codspeed/pull/15)
- Fix typo in release.yml (#14) by @art049 in [#14](https://github.com/CodSpeedHQ/pytest-codspeed/pull/14)


## [2.0.1] - 2023-07-22

### <!-- 0 -->🚀 Features
- Release the package from the CI with trusted provider by @art049
- Add a return type to the benchmark fixture by @art049 in [#13](https://github.com/CodSpeedHQ/pytest-codspeed/pull/13)
- Add support for returning values (#12) by @patrick91 in [#12](https://github.com/CodSpeedHQ/pytest-codspeed/pull/12)

### <!-- 1 -->🐛 Bug Fixes
- Fix setuptools installation with python3.12 by @art049


## [2.0.0] - 2023-07-04

### <!-- 0 -->🚀 Features
- Warmup performance map generation by @art049
- Add some details about the callgraph generation status in the header by @art049
- Test that perf maps are generated by @art049
- Add a local test matrix with hatch by @art049
- Test that benchmark selection with -k works by @art049
- Add support for CPython3.12 and perf trampoline by @art049
- Add introspection benchmarks by @art049 in [#9](https://github.com/CodSpeedHQ/pytest-codspeed/pull/9)

### <!-- 1 -->🐛 Bug Fixes
- Support benchmark.extra_info parameters on the fixture by @art049 in [#10](https://github.com/CodSpeedHQ/pytest-codspeed/pull/10)
- Filter out pytest-benchmark warnings in the tests by @art049

### <!-- 2 -->🏗️ Refactor
- Use the pytest_run_protocol hook for better exec control by @art049

### <!-- 7 -->⚙️ Internals
- Separate the benchmark workflow by @art049 in [#8](https://github.com/CodSpeedHQ/pytest-codspeed/pull/8)
- Bump version to 1.3.0 to trigger the callgraph generation by @art049
- Reuse same test code in the tests by @art049
- Bump linting dependencies by @art049
- Bump precommit in the CI by @art049
- Add python3.12 to the ci matrix by @art049
- Restructure dev dependencies by @art049
- Replace isort by ruff by @art049 in [#11](https://github.com/CodSpeedHQ/pytest-codspeed/pull/11)
- Add discord badge in the readme by @art049


## [1.2.2] - 2022-12-02

### <!-- 0 -->🚀 Features
- Add library metadata in the profile output by @art049 in [#5](https://github.com/CodSpeedHQ/pytest-codspeed/pull/5)


## [1.2.1] - 2022-11-28

### <!-- 1 -->🐛 Bug Fixes
- Support kwargs with the benchmark fixture by @art049 in [#4](https://github.com/CodSpeedHQ/pytest-codspeed/pull/4)


## [1.2.0] - 2022-11-22

### <!-- 1 -->🐛 Bug Fixes
- Avoid wrapping the callable to maintain existing results by @art049
- Disable automatic garbage collection to increase stability by @art049 in [#2](https://github.com/CodSpeedHQ/pytest-codspeed/pull/2)
- Update readme by @art049

### <!-- 7 -->⚙️ Internals
- Update readme by @art049


## [1.1.0] - 2022-11-10

### <!-- 0 -->🚀 Features
- Allow running along with pytest-benchmarks by @art049

### <!-- 1 -->🐛 Bug Fixes
- Fix the release script by @art049
- Make the release script executable by @art049
- Match the test output in any order by @art049

### <!-- 2 -->🏗️ Refactor
- Manage compatibility env in the conftest by @art049

### <!-- 7 -->⚙️ Internals
- Add a pytest-benchmark compatibility test by @art049 in [#1](https://github.com/CodSpeedHQ/pytest-codspeed/pull/1)
- Add more details on the pytest run by @art049
- Continue running on matrix item error by @art049
- Add a CI configuration with pytest-benchmark installed by @art049


[3.2.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.1.2..v3.2.0
[3.1.2]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.1.1..v3.1.2
[3.1.1]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.1.0..v3.1.1
[3.1.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.1.0-beta..v3.1.0
[3.1.0-beta]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0..v3.1.0-beta
[3.0.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0b4..v3.0.0
[3.0.0b4]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0b3..v3.0.0b4
[3.0.0b3]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0b2..v3.0.0b3
[3.0.0b2]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0b1..v3.0.0b2
[3.0.0b1]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v3.0.0b0..v3.0.0b1
[3.0.0b0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v2.2.1..v3.0.0b0
[2.2.1]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v2.2.0..v2.2.1
[2.2.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v2.1.0..v2.2.0
[2.1.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v2.0.1..v2.1.0
[2.0.1]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v2.0.0..v2.0.1
[2.0.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v1.2.2..v2.0.0
[1.2.2]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v1.2.1..v1.2.2
[1.2.1]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v1.2.0..v1.2.1
[1.2.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v1.1.0..v1.2.0
[1.1.0]: https://github.com/CodSpeedHQ/pytest-codspeed/compare/v1.0.4..v1.1.0

<!-- generated by git-cliff -->
