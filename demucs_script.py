import sys
import subprocess

def run_demucs(input_file, output_directory):
    command = [
        'demucs',
        '-o', output_directory,
        input_file
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
    print(stdout)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: demucs_script.py <input_file> <output_directory>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_directory = sys.argv[2]
    run_demucs(input_file, output_directory)