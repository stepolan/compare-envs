import subprocess
import logging
import os
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_pip_list(env_path, env_type):
    """
    Get the list of installed packages in the given environment using pip.

    Args:
    env_path (str): Path to the environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').

    Returns:
    set: A set of installed packages and their versions.
    """
    logging.info(f"Collecting pip list from environment: {env_path}")
    pip_path = os.path.join(env_path, 'bin', 'pip') if env_type == 'virtualenv' else os.path.join(env_path, 'bin', 'pip')
    try:
        result = subprocess.run(
            [pip_path, 'list', '--format=freeze'],
            capture_output=True,
            text=True,
            check=True
        )
        return set(result.stdout.splitlines())
    except subprocess.CalledProcessError as e:
        logging.error(f"Error collecting pip list from {env_path}: {e}")
        return set()

def compare_envs(env1_path, env2_path, env_type):
    """
    Compare the installed packages of two environments and log the differences.

    Args:
    env1_path (str): Path to the first environment.
    env2_path (str): Path to the second environment.
    env_type (str): Type of the environment ('conda' or 'virtualenv').
    """
    env1_packages = get_pip_list(env1_path, env_type)
    env2_packages = get_pip_list(env2_path, env_type)

    only_in_env1 = env1_packages - env2_packages
    only_in_env2 = env2_packages - env1_packages

    logging.info("Comparison complete. Differences:")
    logging.info("\nPackages only in env1:")
    for pkg in sorted(only_in_env1):
        logging.info(pkg)

    logging.info("\nPackages only in env2:")
    for pkg in sorted(only_in_env2):
        logging.info(pkg)

if __name__ == "__main__":
    # Prompt user for environment type
    env_type = input("Enter the environment type (conda/virtualenv): ").strip().lower()

    if env_type not in ['conda', 'virtualenv']:
        logging.error("Invalid environment type. Please enter 'conda' or 'virtualenv'.")
    else:
        # List available environments
        try:
            if env_type == 'conda':
                env_paths = list_conda_envs()
            else:
                env_paths = list_virtualenvs()
        except subprocess.CalledProcessError as e:
            logging.error(f"Error listing environments: {e}")
            env_paths = []

        if not env_paths:
            logging.error(f"No {env_type} environments found.")
        else:
            print(f"Available {env_type} environments:")
            for i, env in enumerate(env_paths):
                print(f"{i + 1}: {env}")

            # Prompt user to select environments
            try:
                env1_index = int(input("Enter the number for the first environment: ")) - 1
                env2_index = int(input("Enter the number for the second environment: ")) - 1

                if env1_index < 0 or env1_index >= len(env_paths) or env2_index < 0 or env2_index >= len(env_paths):
                    logging.error("Invalid selection. Exiting.")
                else:
                    env1_path = env_paths[env1_index]
                    env2_path = env_paths[env2_index]
                    compare_envs(env1_path, env2_path, env_type)
            except ValueError:
                logging.error("Invalid input. Please enter numbers only.")
