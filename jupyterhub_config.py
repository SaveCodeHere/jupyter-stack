# jupyterhub_config.py (Corrected and Simplified)
import os

c = get_config()

# ==============================================================================
# Basic JupyterHub Configuration
# ==============================================================================
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081
c.JupyterHub.base_url = '/hub'

# ==============================================================================
# VOLUME CONFIGURATION (Paths on the HOST machine)
# ==============================================================================
# This is the path on the HOST that you will mount into the Hub and user containers
HOST_NOTEBOOKS_ROOT = '/mnt/host/d/projects/nicstack/data/jupyter/notebooks'

# This is the path INSIDE THE JUPYTERHUB CONTAINER where the above host path will be mounted.
# This path is used by the pre-spawn hook.
HUB_NOTEBOOKS_ROOT = '/notebooks'

# ==============================================================================
# Pre-spawn Hook (Runs inside the Hub container to create directories on the host)
# ==============================================================================
def create_user_directories_on_host(spawner):
    """
    Creates user-specific directories on the host via a mount.
    The user's home directory is created with their UID/GID.
    """
    username = spawner.user.name
    # NOTE: These paths are inside the Hub container, but point to the host via the mount
    #       defined in docker-compose.yml for the jupyterhub service.
    user_dir = os.path.join(HUB_NOTEBOOKS_ROOT, username)
    
    spawner.log.info(f"Pre-spawn hook: ensuring host directory exists at {user_dir}")
    
    try:
        # Create the user's personal directory
        os.makedirs(user_dir, mode=0o755, exist_ok=True)
        # IMPORTANT: Set ownership to the user inside the container (defaults to jovyan:users 1000:100)
        # This assumes your notebook image user is jovyan.
        # If running as root, this step may not be needed, but it is good practice.
        # os.chown(user_dir, 1000, 100) 
        spawner.log.info(f"Successfully created/verified directory for {username}")
    except Exception as e:
        spawner.log.error(f"Error creating host directory for {username}: {e}")

# ==============================================================================
# Spawner: SWARMSPAWNER
# ==============================================================================
c.JupyterHub.spawner_class = 'dockerspawner.SwarmSpawner'

# # --- Mounts Configuration ---
# # This tells the spawner what to mount into each USER'S container.
# c.SwarmSpawner.mounts = [
#     # 1. Mount the user's personal directory (read-write)
#     {
#         'type': 'bind',
#         'source': os.path.join(HOST_NOTEBOOKS_ROOT, '{username}'),
#         'target': '/home/jovyan/work'
#     },
#     # 2. Mount the shared directory (read-only)
#     {
#         'type': 'bind',
#         'source': os.path.join(HOST_NOTEBOOKS_ROOT, 'shared'),
#         'target': '/home/jovyan/shared',
#         'read_only': True
#     },
#     # 3. Mount the datasets directory (read-only)
#     {
#         'type': 'bind',
#         'source': os.path.join(HOST_NOTEBOOKS_ROOT, 'datasets'),
#         'target': '/home/jovyan/datasets',
#         'read_only': True
#     }
# ]


# Assign the pre-spawn hook
c.SwarmSpawner.pre_spawn_hook = create_user_directories_on_host
c.SwarmSpawner.extra_container_spec = {

    # 'env': {
    #     'CUSTOM_VAR': 'value',
    #     'CHOWN_HOME': 'yes',  # Fix ownership issues
    #     'CHOWN_HOME_OPTS': '-R'
    # },
    'mounts': [
        {
            'source': f'/mnt/host/d/projects/nicstack/data/jupyter/notebooks/shared',
            'target': '/home/jovyan/shared',
            'type': 'bind'
        }
    ],
    
}

# --- General Settings ---
c.SwarmSpawner.image = 'nicstack/notebook:latest'
c.SwarmSpawner.network_name = 'nicstack_reverseproxy_network'
c.SwarmSpawner.notebook_dir = '/home/jovyan' # The user starts in their personal directory
c.SwarmSpawner.default_url = '/lab'

# ==============================================================================
# Authenticator, Persistence, Logging  
# ==============================================================================
c.JupyterHub.authenticator_class = 'dummy'
c.DummyAuthenticator.password = os.getenv('JUPYTERHUB_ADMIN_PASSWORD')
c.Authenticator.admin_users = {'admin'}
c.Authenticator.allowed_users = {'admin', "testuser", "poccers", "testuser2"}

c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/jupyterhub_cookie_secret'

# Set log levels for debugging
c.Application.log_level = 'DEBUG'
c.JupyterHub.log_level = 'DEBUG'
c.SwarmSpawner.log_level = 'DEBUG'