import sys
from demucs.separate import main as demucs_main

def run_demucs(input_file, output_directory):
    sys.argv = ['demucs', '-o', output_directory, input_file]
    demucs_main()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: demucs_script.py <input_file> <output_directory>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_directory = sys.argv[2]
    run_demucs(input_file, output_directory)