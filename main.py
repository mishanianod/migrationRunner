import os
import subprocess
import threading
import multiprocessing
from flask import Flask, render_template, jsonify, request, send_file
import git

GIT_PASSWORD = os.environ.get('GIT_PASSWORD')

# Configuration
node_repo_url = f"https://asaedi:{GIT_PASSWORD}@bitbucket.org/employeeportal/backend.git"
python_repo_url = f"https://asaedi:{GIT_PASSWORD}@bitbucket.org/employeeportal/migration-scripts.git"

node_repo_dir = "/node_repo"
python_repo_dir = "/python_repo"

# Clone repositories
def clone_repo(url, directory):
    if not os.path.exists(directory):
        git.Repo.clone_from(url, directory)
    else:
        print(f"Directory {directory} already exists. Pulling latest changes.")
        repo = git.Repo(directory)
        repo.remotes.origin.pull()


# clone_repo(node_repo_url, node_repo_dir)
# clone_repo(python_repo_url, python_repo_dir)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Store process objects
processes: dict = {
    'node': None,
    'python': None
}

# Function to run commands
def run_command(command, cwd, log_file):
    with open(log_file, 'w') as f:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        for line in process.stdout or '':
            f.write(line)
            f.flush()
        process.wait()

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pull/<repo>', methods=['POST'])
def pull(repo):
    if repo == 'node':
        clone_repo(node_repo_url, node_repo_dir)
    else:
        clone_repo(python_repo_url, python_repo_dir)
    return jsonify({"status": "pulled"})

@app.route('/logs/<repo>')
def logs(repo):
    log_file = f"{repo}_log.txt"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return ''.join(f.readlines
                            ()[-100:])

    return ""

# route to download the log file
@app.route('/download/<repo>')
def download(repo):
    log_file = f"{repo}_log.txt"
    if os.path.exists(log_file):
        return send_file(log_file, as_attachment=True)
    else:
        return jsonify({"status": "Log file not found"})
    

@app.route('/run/<repo>', methods=['POST'])
def run(repo):
    global processes
    print(processes[repo])
    if processes[repo] is None or not processes[repo].is_alive():
        if repo == 'node':
            command = "npm install && npm run dev"
            cwd = node_repo_dir
        else:
            command = "pip install -r requirements.txt && python migration.py"
            cwd = python_repo_dir

        log_file = f"{repo}_log.txt"
        # processes[repo] = threading.Thread(target=run_command, args=(command, cwd, log_file))
        processes[repo] = multiprocessing.Process(target=run_command, args=(command, cwd, log_file))
        processes[repo].start()
        return jsonify({"status": "started"})
    return jsonify({"status": "already running"})

@app.route('/terminate/<repo>', methods=['POST'])
def terminate(repo):
    global processes
    if processes[repo] is not None and processes[repo].is_alive():
        # This is a simplified termination. In a real-world scenario, you'd want to handle this more gracefully.
        processes[repo].terminate()
        processes[repo] = None

        if repo == 'node':
            os.system("kill -9 $(lsof -t -i:8081)")

        return jsonify({"status": "terminated"})
    return jsonify({"status": "not running"})

@app.route('/env')
def env():
    return render_template("env.html", node_env=get_env_content(node_repo_dir), python_env=get_env_content(python_repo_dir))

@app.route('/companies')
def companies():
    return render_template("companies.html")

@app.route('/companies_json')
def load_():
    companies_file = "companies.json"
    if os.path.exists(companies_file):
        with open(companies_file, 'r') as f:
            return f.read()
    return "[]"

@app.route('/companies_json', methods=['POST'])
def save_companies():
    companies = request.form['companies']
    companies_file = "companies.json"
    with open(companies_file, 'w') as f:
        f.write(companies)
    return jsonify({"status": "Companies saved successfully"})


@app.route('/config')
def config():
    return render_template("config.html")

@app.route('/config_json')
def load_config():
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return f.read()
    return "{}"

@app.route('/config_json', methods=['POST'])
def save_config():
    configs = request.form['config']
    config_file = "config.json"
    with open(config_file, 'w') as f:
        f.write(configs)
    return jsonify({"status": "Config saved successfully"})

def get_env_content(repo_dir):
    env_file = os.path.join(repo_dir, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            return f.read()
    return ""

@app.route('/save_env/<repo>', methods=['POST'])
def save_env(repo):
    content = request.form['content']
    repo_dir = node_repo_dir if repo == 'node' else python_repo_dir
    env_file = os.path.join(repo_dir, '.env')
    with open(env_file, 'w') as f:
        f.write(content)
    return jsonify({"status": "Environment variables saved successfully"})

@app.route("/clear/<repo>", methods=['POST'])
def clear_logs(repo):
    log_file = f"{repo}_log.txt"
    if os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("")
    return jsonify({"status": "Logs cleared"})

@app.route('/status')
def status():
    global processes
    return jsonify({
        "node": "running" if processes['node'] is not None and processes['node'].is_alive() else "stopped",
        "python": "running" if processes['python'] is not None and processes['python'].is_alive() else "stopped"
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

