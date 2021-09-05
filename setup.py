from setuptools import setup, find_packages

setup(
    author="Charles Titus",
    author_email="charles.titus@nist.gov",
    install_requires=["bluesky", "ophyd", "numpy"],
    entry_points={"pytest11": ["sst_base_experiment = sst_base.tests.test_experiment_setup"]},
    name="sst_base",
    use_scm_version=True,
    packages=find_packages()
)
