import os
import subprocess

TAG = 'psychobotserver'

try:
    subprocess.check_call(['docker', 'build', '-t', TAG, '.'])
    print(f"Docker image '{TAG}' built successfully.")
except subprocess.CalledProcessError as e:
    print(f"Failed to build Docker image '{TAG}': {e}")

try:
    subprocess.check_call(['docker', 'tag', 'psychobotserver', 'motheenb/psychobotserver:latest'])
    print('Docker image tagged successfully!')
except subprocess.CalledProcessError as e:
    print('Failed to tag!')

try:
    subprocess.check_call(['docker', 'push', 'motheenb/psychobotserver'])
    print('Successfully pushed image to server!')
except subprocess.CalledProcessError as e:
    print('Failed to push!')