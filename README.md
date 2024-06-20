# Compare Envs

## Overview

This script compares two Python environments (Conda or virtualenv) and lists all top-level packages, highlighting unique packages for each environment. It also compares environment variables and startup scripts. Additionally, it compares packages listed by Conda and Pip within the same environment.

## Installation

To set up the environment for running this script, use the provided `environment.yml` file.

1. Create the Conda environment:

    ```sh
    conda env create -f environment.yml
    ```

2. Activate the environment:

    ```sh
    conda activate compare-envs
    ```

3. If there are additional packages listed in a `requirements.txt` file, install them:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

Run the script to compare two environments. It lists all top-level packages and highlights the unique ones in bright green. It also compares environment variables and startup scripts if they exist. Additionally, it compares packages listed by Conda and Pip within the same environment.

```sh
python compare_envs.py
```

### Script Prompts

1. **Environment Type**: Enter the environment type (c for Conda, v for virtualenv). The default is Conda.

2. **Environment Selection**: The script lists available environments. Enter the number corresponding to the environments you want to compare.

### Example Output

The script will display:

- All packages in each environment, with unique packages highlighted in bright green.
- Environment variables specific to each environment.
- Startup scripts specific to each environment.
- Comparison of packages listed by Conda and Pip within the same environment.

The results will also be saved in a file named `<env1 name>_vs_<env2 name>.txt`.

### Notes

- If `pipdeptree` is not installed in the target environments, the script will automatically install it.
- Ensure you have the necessary permissions to activate and modify the target environments.

## License

This project is licensed under the Apache 2.0 License.