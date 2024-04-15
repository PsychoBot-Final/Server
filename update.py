import os
import subprocess

TAG = 'psychobotserver'

# PROCESSES = {
#     'BUILD:': ['docker', 'build', '-t', TAG, '.'],
#     'TAG:': ['docker', 'tag', 'psychobotserver', 'motheenb/psychobotserver:latest'],
#     'PUSH:': ['docker', 'push', 'motheenb/psychobotserver']
# }

# for step, process in PROCESSES.items():
#     try:
#         print(f'-->{step}<--')
#         subprocess.check_call(process)
#         print()
#     except subprocess.CalledProcessError as e:
#         print('Error!')

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