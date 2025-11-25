import os
from pathlib import Path  # to handle path issues, it identifies which type of system paath it is windows, linux or Mac
import logging

logging.basicConfig(level=logging.INFO, format= '[%(asctime)s] : %(message)s:')  # logging info - will return ascii time and logging message

project_name = "METLN"

list_of_files = [
    ".github/workflows/.gitkeep",  # gitkeep if any empty folder it identifies that
    ".gitignore",
    f"src/{project_name}/__init__.py",  # constructor file
    f"src/{project_name}/utils/db.py",
    f"src/{project_name}/extract.py",
    f"src/{project_name}/transform.py",
    f"src/{project_name}/load.py",
    f"src/{project_name}/pipeline.py",
    f"src/{project_name}/timeseries.py",
    "data/raw/__init__.py",
    "data/processed/__init__.py",
    "config/config.yaml",
    "dvc.yaml",
    "requirements.txt",
    "setup.py",
    "research/trails.ipynb"  # for experimentation purpose - optional
]

for filepath in list_of_files:
    filepath = Path(filepath)
    # separate folder name and file names
    filedir, filename = os.path.split(filepath)

    # check if folder is not empty
    if filedir != "":
        os.makedirs(filedir, exist_ok= True)
        logging.info(f"Creating directory {filedir} for the file {filename}")

    # Check if the file is present and what if the filesize (like if any content exists in file)
    if (not (os.path.exists(filename)) or (os.path.getsize(filename) == 0)):
        with open(filepath,"w") as f:
            pass
            logging.info(f"Creating empty file {filepath}")
    else:
        logging.info(f"The file {filename} alraedy exists")
