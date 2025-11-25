import setuptools

with open("README.md","r",encoding='utf-8') as f:
    long_description = f.read()

__version__ = "0.0.0"

REPO_NAME = "MTLN_Project"
AUTHOR_USER_NAME = "AshishJaiswal25"
SRC_REPO = "METLN"
AUTHOR_EMAIL = "zadane.m@northeastern.com" 

setuptools.setup(
    name  = SRC_REPO,
    version=__version__,
    author = AUTHOR_USER_NAME,
    author_email = AUTHOR_EMAIL,
    description= "Python Project for Maine Trust Local News",
    long_description= long_description,
    long_description_content = "text/markdown",
    url = f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}",
    project_urls = {
        "Bug Tracker": f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}/issues"
    },
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src")
)
