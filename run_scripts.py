import subprocess

def run_script(script_name):
    try:
        result = subprocess.run(['python', script_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
        print(result.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"Failed to run {script_name}: {e}")

if __name__ == "__main__":
    run_script('places.py')
    run_script('filteredReviews.py')
