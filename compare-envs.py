import subprocess
import logging
import os
import glob
from colorama import Fore, Style, init
import getpass

# Initialize colorama
init(autoreset=True)

import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# File handler (detailed logging)
file_handler = logging.FileHandler('compare-envs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Console handler (less detailed)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def create_results_dir():
    """Create the results directory if it does not exist."""
    results_dir = './results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    return results_dir

def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')

def list_conda_envs():
    """
    List all Conda environments available on the system.

    Returns:
    list: A list of paths to Conda environments.
    """
    result = subprocess.run(['conda', 'env', 'list'], capture_output=True, text=True, check=True)
    lines = result.stdout.splitlines()
    env_paths = []
    for line in lines:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split()
        env_paths.append(parts[-1])
    return env_paths

def list_virtualenvs():
    """
    List all virtualenv environments available on the system.

    Returns:
    list: A list of paths to virtualenv environments.
    """
    venv_dir = os.path.expanduser('~/.virtualenvs')
    env_paths = glob.glob(os.path.join(venv_dir, '*'))
    return env_paths

def truncate_env_name(env_name, length=20):
    """
    Truncate the environment name to a specific length.

    Args:
    env_name (str): The environment name.
    length (int): The maximum length of the truncated name.

    Returns:
    str: The truncated environment name.
    """
    if len(env_name) > length:
        return env_name[:length-3] + '...'
    return env_name

def redact_username(path):
    """
    Redact the username from the given path.

    Args:
    path (str): The path to redact.

    Returns:
    str: The path with the username redacted.
    """
    username = getpass.getuser()
    return path.replace(username, '%un%')

def truncate_path(path, length=50):
    """
    Truncate the path to a specific length.

    Args:
    path (str): The path.
    length (int): The maximum length of the truncated path.

    Returns:
    str: The truncated path.
    """
    if len(path) > length:
        return path[:length-3] + '...'
    return path

def list_and_display_envs(env_type):
    """
    List available environments and display them in a table format.

    Args:
    env_type (str): Type of the environment ('conda' or 'virtualenv').

    Returns:
    list: A list of paths to environments.
    """
    if env_type == 'conda':
        env_paths = list_conda_envs()
    else:
        env_paths = list_virtualenvs()

    if not env_paths:
        logging.error(f"No {env_type} environments found.")
        return []

    clear_screen()
    print(f"{Fore.GREEN}Available {env_type} environments:{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}+----+-----------------------+----------------------------------------------------+{Style.RESET_ALL}")
    print(f"{Fore.CYAN}| #  | Env Name              | Path (redacted username)                           |{Style.RESET_ALL}")
    print(f"{Fore.CYAN}|----+-----------------------+----------------------------------------------------+{Style.RESET_ALL}")

    for i, env in enumerate(env_paths):
        env_name = os.path.basename(env)
        truncated_env_name = truncate_env_name(env_name, length=20)
        redacted_env_path = redact_username(env)
        truncated_env_path = truncate_path(redacted_env_path, length=50)
        print(f"{Fore.CYAN}|{Fore.YELLOW} {i + 1:<3}{Fore.CYAN}| {Fore.YELLOW}{truncated_env_name:<21} {Fore.CYAN}| {Fore.YELLOW}{truncated_env_path:<50} {Fore.CYAN}| {Style.RESET_ALL}")

    print(f"{Fore.CYAN}|----+-----------------------+----------------------------------------------------+{Style.RESET_ALL}")

    return env_paths

def install_pipdeptree(env_path, env_type):
    """
    Install pipdeptree in the given environment if not already installed.

    Args:
    env_path (str): Path to the environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').
    """
    logging.info(f"Checking if pipdeptree is installed in environment: {env_path}")
    try:
        if env_type == 'conda':
            check_cmd = f"conda run -n {os.path.basename(env_path)} python -m pipdeptree --version"
        else:
            check_cmd = f"source {env_path}/bin/activate && python -m pipdeptree --version"

        result = subprocess.run(
            check_cmd,
            shell=True,
            capture_output=True,
            text=True,
            executable="/bin/bash"
        )

        if result.returncode != 0:
            logging.info(f"pipdeptree not found. Installing pipdeptree in environment: {env_path}")
            if env_type == 'conda':
                install_cmd = f"conda run -n {os.path.basename(env_path)} pip install pipdeptree"
            else:
                install_cmd = f"source {env_path}/bin/activate && pip install pipdeptree"

            subprocess.run(
                install_cmd,
                shell=True,
                check=True,
                executable="/bin/bash"
            )
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking/installing pipdeptree in {env_path}: {e}")

def get_env_variables(env_path):
    """
    Get environment variables specific to the given environment.

    Args:
    env_path (str): Path to the environment.

    Returns:
    dict: A dictionary of environment variables.
    """
    env_vars_path = os.path.join(env_path, 'etc', 'conda', 'activate.d', 'env_vars.sh')
    env_vars = {}
    if os.path.exists(env_vars_path):
        with open(env_vars_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    else:
        logging.warning(f"No environment variables file found at {env_vars_path}")
    return env_vars

def get_startup_scripts(env_path):
    """
    Get startup scripts specific to the given environment.

    Args:
    env_path (str): Path to the environment.

    Returns:
    list: A list of startup scripts.
    """
    startup_scripts_dir = os.path.join(env_path, 'etc', 'conda', 'activate.d')
    if os.path.exists(startup_scripts_dir):
        return [os.path.join(startup_scripts_dir, f) for f in os.listdir(startup_scripts_dir) if f.endswith('.sh')]
    else:
        logging.warning(f"No startup scripts directory found at {startup_scripts_dir}")
        return []

def normalize_package_name(name):
    """
    Normalize package name by converting to lowercase and replacing underscores and hyphens with periods.

    Args:
    name (str): The package name.

    Returns:
    str: The normalized package name.
    """
    return name.lower().replace('_', '.').replace('-', '.')

def compare_conda_and_pip_packages(env_path):
    """
    Compare packages listed by Conda and Pip within the same environment.

    Args:
    env_path (str): Path to the environment.
    """
    logging.info(f"Comparing Conda and Pip packages in environment: {env_path}")
    conda_packages = {}
    pip_packages = {}

    try:
        # Get Conda packages
        result = subprocess.run(['conda', 'list', '-n', os.path.basename(env_path)], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if not line.startswith('#'):
                parts = line.split()
                if len(parts) > 1:
                    conda_packages[normalize_package_name(parts[0])] = parts[1]

        # Get Pip packages
        result = subprocess.run(['conda', 'run', '-n', os.path.basename(env_path), 'pip', 'list'], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines()[2:]:  # Skip header lines
            parts = line.split()
            if len(parts) > 1:
                pip_packages[normalize_package_name(parts[0])] = parts[1]

        only_in_conda = set(conda_packages) - set(pip_packages)
        only_in_pip = set(pip_packages) - set(conda_packages)
        in_both = set(conda_packages) & set(pip_packages)
        different_versions = {pkg for pkg in in_both if conda_packages[pkg] != pip_packages[pkg]}

        print(f"\n{Fore.GREEN}Comparison of Conda and Pip packages in environment: {os.path.basename(env_path)}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}Packages only in Conda:{Style.RESET_ALL}\n")
        for pkg in sorted(only_in_conda):
            print(f"{Fore.RED}{pkg}=={conda_packages[pkg]}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}Packages only in Pip:{Style.RESET_ALL}\n")
        for pkg in sorted(only_in_pip):
            print(f"{Fore.RED}{pkg}=={pip_packages[pkg]}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}Packages in both but different versions:{Style.RESET_ALL}\n")
        for pkg in sorted(different_versions):
            print(f"{Fore.YELLOW}{pkg}=={conda_packages[pkg]} (Conda) != {pip_packages[pkg]} (Pip){Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}Packages in both with same versions:{Style.RESET_ALL}\n")
        for pkg in sorted(in_both - different_versions):
            print(f"{Fore.GREEN}{pkg}=={conda_packages[pkg]}{Style.RESET_ALL}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error comparing Conda and Pip packages in {env_path}: {e}")

def get_dependency_tree(env_path, env_type):
    """
    Get the dependency tree of the installed packages in the given environment using pipdeptree.

    Args:
    env_path (str): Path to the environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').

    Returns:
    str: The dependency tree as a string.
    """
    logging.info(f"Getting dependency tree for environment: {env_path}")
    try:
        # Activate the environment and run pipdeptree
        if env_type == 'conda':
            activate_cmd = f"conda run -n {os.path.basename(env_path)} pipdeptree"
        else:
            activate_cmd = f"source {env_path}/bin/activate && pipdeptree"

        logging.info(f"Running command: {activate_cmd}")
        result = subprocess.run(
            activate_cmd,
            shell=True,
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            text=True,
            executable="/bin/bash"
        )

        # Log the output
        logging.debug(f"pipdeptree output for {env_path}: {result.stdout}")
        logging.debug(f"pipdeptree errors for {env_path}: {result.stderr}")

        if result.returncode != 0:
            logging.error(f"Error getting dependency tree: {result.stderr}")
            return "Error getting dependency tree."

        return result.stdout

    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting dependency tree from {env_path}: {e}")
        return "Error getting dependency tree."

def compare_envs(env1_path, env2_path, env_type, env1_name, env2_name):
    """
    Compare the top-level installed packages, environment variables, startup scripts, and dependency trees of two environments and log the differences.

    Args:
    env1_path (str): Path to the first environment.
    env2_path (str): Path to the second environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').
    env1_name (str): Name of the first environment.
    env2_name (str): Name of the second environment.
    """
    clear_screen()

    results_dir = create_results_dir()

    env1_packages = get_top_level_packages(env1_path, env_type)
    env2_packages = get_top_level_packages(env2_path, env_type)

    only_in_env1 = set(env1_packages) - set(env2_packages)
    only_in_env2 = set(env2_packages) - set(env1_packages)
    in_both = set(env1_packages) & set(env2_packages)
    different_versions = {pkg for pkg in in_both if env1_packages[pkg] != env2_packages[pkg]}

    env1_vars = get_env_variables(env1_path)
    env2_vars = get_env_variables(env2_path)

    env1_scripts = get_startup_scripts(env1_path)
    env2_scripts = get_startup_scripts(env2_path)

    results = []

    # Color coding explanation in a box
    column_width = 40
    border_color = Fore.BLUE

    clear_screen()

    results.append(f"{border_color}+{'-' * (2 * column_width + 1)}+{Style.RESET_ALL}")
    results.append(f"{border_color}| {Style.RESET_ALL}{'Color Coding Explanation':<{2 * column_width - 1}} {border_color}|{Style.RESET_ALL}")
    results.append(f"{border_color}+{'-' * (2 * column_width + 1)}+{Style.RESET_ALL}")
    results.append(f"{border_color}| {Fore.RED}Red: {Style.RESET_ALL}Package unique to one environment {' ' * (2 * column_width - 40)} {border_color}|")
    results.append(f"{border_color}| {Fore.YELLOW}Yellow: {Style.RESET_ALL}Same package, different versions {' ' * (2 * column_width - 42)} {border_color}|")
    results.append(f"{border_color}| {Fore.GREEN}Green: {Style.RESET_ALL}Same package, same version {' ' * (2 * column_width - 35)} {border_color}|")
    results.append(f"{border_color}+{'-' * (2 * column_width + 1)}+{Style.RESET_ALL}\n")

    # Append table header to results
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    results.append(f"{border_color}| {Fore.WHITE}{env1_name:<{column_width - 2}} {border_color}| {Fore.WHITE}{env2_name:<{column_width - 2}} {border_color}|{Style.RESET_ALL}")
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")

    # Section 1: Same Packages/Versions
    results.append(f"{border_color}| {Fore.WHITE}{'Same Packages/Versions':<{2 * column_width - 1}} {border_color}|{Style.RESET_ALL}")
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    for pkg in sorted(in_both - different_versions):
        results.append(f"{border_color}| {Fore.GREEN}{pkg}=={env1_packages[pkg]:<{column_width - len(pkg) - 4}} {border_color}| {Fore.GREEN}{pkg}=={env2_packages[pkg]:<{column_width - len(pkg) - 4}} {border_color}|{Style.RESET_ALL}")

    # Section 2: Same Package/Different Versions
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    results.append(f"{border_color}| {Fore.WHITE}{'Same Package/Different Versions':<{2 * column_width - 1}} {border_color}|{Style.RESET_ALL}")
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    for pkg in sorted(different_versions):
        results.append(f"{border_color}| {Fore.YELLOW}{pkg}=={env1_packages[pkg]:<{column_width - len(pkg) - 4}} {border_color}| {Fore.YELLOW}{pkg}=={env2_packages[pkg]:<{column_width - len(pkg) - 4}} {border_color}|{Style.RESET_ALL}")

    # Section 3: Unique Packages
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    results.append(f"{border_color}| {Fore.WHITE}{'Unique Packages':<{2 * column_width - 1}} {border_color}|{Style.RESET_ALL}")
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")
    unique_env1 = sorted(list(only_in_env1))
    unique_env2 = sorted(list(only_in_env2))
    max_unique = max(len(unique_env1), len(unique_env2))
    for i in range(max_unique):
        pkg_env1 = f"{unique_env1[i]}=={env1_packages[unique_env1[i]]}" if i < len(unique_env1) else ""
        pkg_env2 = f"{unique_env2[i]}=={env2_packages[unique_env2[i]]}" if i < len(unique_env2) else ""
        results.append(f"{border_color}| {Fore.RED}{pkg_env1:<{column_width - 2}} {border_color}| {Fore.RED}{pkg_env2:<{column_width - 2}} {border_color}|{Style.RESET_ALL}")

    # End of the table
    results.append(f"{border_color}+{'-' * column_width}+{'-' * column_width}+{Style.RESET_ALL}")

    # Append environment variables and startup scripts to results
    results.append(f"\n{Fore.YELLOW}Environment variables in {env1_name}:{Style.RESET_ALL}\n")
    if env1_vars:
        for var, val in env1_vars.items():
            results.append(f"{var}={val}")
    else:
        results.append("No environment variables found.")

    results.append(f"\n{Fore.YELLOW}Environment variables in {env2_name}:{Style.RESET_ALL}\n")
    if env2_vars:
        for var, val in env2_vars.items():
            results.append(f"{var}={val}")
    else:
        results.append("No environment variables found.")

    results.append(f"\n{Fore.YELLOW}Startup scripts in {env1_name}:{Style.RESET_ALL}\n")
    if env1_scripts:
        for script in env1_scripts:
            results.append(script)
    else:
        results.append("No startup scripts found.")

    results.append(f"\n{Fore.YELLOW}Startup scripts in {env2_name}:{Style.RESET_ALL}\n")
    if env2_scripts:
        for script in env2_scripts:
            results.append(script)
    else:
        results.append("No startup scripts found.")

    # Write results to a file in the results directory
    results_file = os.path.join(results_dir, f"{env1_name}_vs_{env2_name}.txt")
    with open(results_file, "w") as f:
        for line in results:
            f.write(line + "\n")

    # Print results to the console
    for line in results:
        print(line)

    print(f"\n{Fore.CYAN}Note: Detailed logs are available in the 'compare-envs.log' file.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Note: Comparisons are saved in the './results' directory.{Style.RESET_ALL}")


    print(f"\n{Fore.BLUE}+{'-' * 39}+{Style.RESET_ALL}")
    print(f"{Fore.BLUE}|  {Fore.YELLOW}    Initial Comparison Complete!     {Fore.BLUE}|{Style.RESET_ALL}")
    print(f"{Fore.BLUE}+{'-' * 39}+{Style.RESET_ALL}\n")

    # Prompt user if they want to see the full dependency tree
    show_deps = input(f"{Fore.CYAN}Do you want to see the full dependency tree for the environments? (y/n) [default: n]: {Style.RESET_ALL}").strip().lower() or 'n'
    if show_deps == 'y':
        display_dependency_trees(env1_path, env2_path, env_type, env1_name, env2_name)

    # Prompt user if they want to compare Conda and Pip packages
    compare_conda_pip = input(f"{Fore.CYAN}Do you want to compare Conda and Pip packages in the environments? (y/n) [default: n]: {Style.RESET_ALL}").strip().lower() or 'n'
    if compare_conda_pip == 'y':
        compare_conda_and_pip_packages(env1_path)
        compare_conda_and_pip_packages(env2_path)

def get_top_level_packages(env_path, env_type):
    """
    Get the list of top-level installed packages in the given environment using pipdeptree.

    Args:
    env_path (str): Path to the environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').

    Returns:
    dict: A dictionary of top-level installed packages and their versions.
    """
    logging.info(f"Activating environment: {env_path}")
    top_level_packages = {}

    try:
        # Ensure pipdeptree is installed
        install_pipdeptree(env_path, env_type)

        # Activate the environment and run pipdeptree
        if env_type == 'conda':
            activate_cmd = f"conda run -n {os.path.basename(env_path)} python -m pipdeptree --warn silence"
        else:
            activate_cmd = f"source {env_path}/bin/activate && pipdeptree --warn silence"

        logging.info(f"Running command: {activate_cmd}")
        result = subprocess.run(
            activate_cmd,
            shell=True,
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            text=True,
            executable="/bin/bash"
        )

        # Log the output
        logging.debug(f"pipdeptree output for {env_path}: {result.stdout}")
        logging.debug(f"pipdeptree errors for {env_path}: {result.stderr}")

        # Process the captured output internally
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Check if line represents a top-level package
                if not line.startswith(('│', '├──', '└──')):
                    if '==' in line or '@' in line:
                        # Extract package name and version
                        package = line.split('==')[0].split('@')[0].strip()
                        version = line.split('==')[-1] if '==' in line else 'unknown'
                        top_level_packages[package] = version

        return top_level_packages
    except subprocess.CalledProcessError as e:
        logging.error(f"Error collecting top-level pip list from {env_path}: {e}")
        return {}

def display_dependency_trees(env1_path, env2_path, env_type, env1_name, env2_name):
    """
    Display the full dependency trees for the given environments.

    Args:
    env1_path (str): Path to the first environment.
    env2_path (str): Path to the second environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').
    env1_name (str): Name of the first environment.
    env2_name (str): Name of the second environment.
    """
    env1_deps = get_dependency_tree(env1_path, env_type)
    env2_deps = get_dependency_tree(env2_path, env_type)
    
    print(f"\n{Fore.YELLOW}Dependency tree in {env1_name}:{Style.RESET_ALL}\n")
    print(env1_deps)
    
    print(f"\n{Fore.YELLOW}Dependency tree in {env2_name}:{Style.RESET_ALL}\n")
    print(env2_deps)

if __name__ == "__main__":
    clear_screen()
    print(f"{Fore.BLUE}{Style.BRIGHT}Welcome to the Environment Comparison Tool!{Style.RESET_ALL}\n")

    # Prompt user for environment type
    env_type = input(f"{Fore.CYAN}Enter the environment type (c for conda, v for virtualenv) [default: c]: {Style.RESET_ALL}").strip().lower() or 'c'
    print()

    if env_type not in ['c', 'v']:
        logging.error(f"{Fore.RED}Invalid environment type. Please enter 'c' or 'v'.{Style.RESET_ALL}")
    else:
        env_type = 'conda' if env_type == 'c' else 'virtualenv'
        # List available environments and display them in a table
        env_paths = list_and_display_envs(env_type)

        if env_paths:
            print()
            # Prompt user to select environments
            try:
                env1_index = int(input(f"{Fore.CYAN}Enter the number for the first environment: {Style.RESET_ALL}")) - 1
                env2_index = int(input(f"{Fore.CYAN}Enter the number for the second environment: {Style.RESET_ALL}")) - 1
                print()

                if env1_index < 0 or env1_index >= len(env_paths) or env2_index < 0 or env2_index >= len(env_paths):
                    logging.error(f"{Fore.RED}Invalid selection. Exiting.{Style.RESET_ALL}")
                else:
                    env1_path = env_paths[env1_index]
                    env2_path = env_paths[env2_index]
                    env1_name = os.path.basename(env1_path)
                    env2_name = os.path.basename(env2_path)
                    compare_envs(env1_path, env2_path, env_type, env1_name, env2_name)

                    print(f"\n{Fore.BLUE}+---------------------------------------+{Style.RESET_ALL}")
                    print(f"{Fore.BLUE}|  {Fore.YELLOW}        Comparison Complete!       {Fore.BLUE}  |{Style.RESET_ALL}")
                    print(f"{Fore.BLUE}+---------------------------------------+{Style.RESET_ALL}\n")

            except ValueError:
                logging.error(f"{Fore.RED}Invalid input. Please enter numbers only.{Style.RESET_ALL}")