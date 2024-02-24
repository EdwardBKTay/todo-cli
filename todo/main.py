import typer
import os
from rich import print
from typing_extensions import Annotated, Optional
import json
import datetime
from tabulate import tabulate

app = typer.Typer(no_args_is_help=True)

class Task:
    def __init__(self, name: str, priority: Optional[str] = None, est_min: Optional[str] = None):
        self.name = name
        self.set_priority(priority)
        self.set_completion_min(est_min)
        self.set_date()
    
    def set_priority(self, priority: Optional[str] = None):
        if priority is None:
            self.priority = priority
            return
        priority = priority.upper()
        if len(priority) != 1 or not priority.isalpha() or not "A" <= priority <= "Z":
            print("[bold red]Priority must be a single alphabet character (A-Z).[/bold red]")
            raise typer.Exit(code=1)
        self.priority = priority
        
    def set_completion_min(self, est_min: Optional[str] = None):
        if est_min is None:
            self.est_min = est_min
            return
        else:
            if est_min.isdigit():
                est_min_int = int(est_min)
                if est_min_int < 0:
                    print("[bold red]Estimated completion minutes must be a positive integer.[/bold red]")
                    raise typer.Exit(code=1)
                else:
                    self.est_min = str(est_min_int)
            else:
                print("[bold red]Estimated completion minutes must be a positive integer.[/bold red]")
                raise typer.Exit(code=1)
        
    def set_date(self):
        self.date = datetime.date.today()

def save_todo_config(root_dir: str, dir_name: str, todo_file: str, done_file: str):
    """
    Save the todo configuration to a file in the current working directory.
    """
    dir_path = os.path.join(root_dir, dir_name)
    todo_file_path = os.path.join(dir_path, todo_file)
    done_file_path = os.path.join(dir_path, done_file)
    
    config = {
        "todo_dir": dir_path,
        "todo_file": todo_file_path,
        "done_file": done_file_path
    }
    
    with open (".todo_config_json", "w") as f:
        f.write(json.dumps(config))
        
def load_config():
    """
    Load the todo configuration from the current working directory.
    """
    try:
        with open(".todo_config.json", "r") as f:
            data = json.loads(f.read())
            for key in ["todo_dir", "todo_file", "done_file"]:
                if key not in data:
                    print(f"[bold red]Missing {key} in .todo_config.json[/bold red]")
                    raise typer.Exit(code=1)
            return data
    except FileNotFoundError:
        print("[bold red]No todo configuration found. Please run `todo init` first.[/bold red]")
        raise typer.Exit(code=1)

@app.command()
def init(dir_name: Annotated[str, typer.Argument(help="The name of the todo directory")] = ".todo", todo_file: Annotated[str, typer.Argument(help="The name of the todo file")] = "todo.txt", done_file: Annotated[str, typer.Argument(help="The name of the done file")] = "done.txt"):
    """
    Initialize a new directory with a todo and done file.
    """
    
    root_dir = os.path.expanduser("~")
    todo_dir = os.path.join(root_dir, dir_name)
    
    if os.path.exists(todo_dir):
        print(f"[bold red]{dir_name} already exists in {root_dir}[/bold red]")
        raise typer.Exit(code=1)
    
    if not todo_file.endswith(".txt") or not done_file.endswith(".txt"):
        print("[bold red]todo_file and done_file must ends with .txt[/bold red]")
        raise typer.Exit(code=1)
    
    try:
        os.mkdir(os.path.join(root_dir, dir_name))
        with open(os.path.join(root_dir, dir_name, todo_file), "w"):
            pass
        with open(os.path.join(root_dir, dir_name, done_file), "w"):
            pass
        
        save_todo_config(root_dir, dir_name, todo_file, done_file)
        
        print(f"[bold green]Create {todo_file} and {done_file} in {root_dir}/{dir_name}[/bold green]")
    except FileExistsError:
        print(f"[bold red]{dir_name} already exists in {root_dir}[/bold red]")
        raise typer.Exit(code=1)
    
@app.command()
def add(task_name: Annotated[str, typer.Argument(help="The name of the task")], priority: Annotated[Optional[str], typer.Argument(help="Priority of the task (A-Z)")] = None, estimated_completion_minutes: Annotated[Optional[str], typer.Argument(help="Estimated completion minutes")] = None):
    """
    Add a new task to the todo file.
    """
    config = load_config()
    task = Task(task_name, priority, estimated_completion_minutes)
    task_details = f"{task.name},{task.priority},{task.est_min},{task.date}\n"
    with open(config["todo_file"], "a") as f:
        f.write(task_details)
    print(f"[bold green]Task added: {task_name}[/bold green]")
    
@app.command()
def list():
    """
    List all tasks in the todo file.
    """
    config = load_config()
    with open(config["todo_file"], "r") as f:
        tasks = [line.strip().split(",") for line in f.readlines()]
        
    if not tasks:
        print("[bold green]No tasks to show[/bold green]")
    else:
        headers = ["ID", "Task", "Priority", "Estimated Completion Minutes", "Date"]
        tasks_with_id = [[str(i+1)] + task for i, task in enumerate(tasks)]
        
        def prioritize_today(task):
            today = datetime.date.today().strftime("%Y-%m-%d")
            if task[4] == today:
                return (0, task[2], task[3])
            else:
                return (1, task[4], task[2], task[3])
        
        sorted_tasks = sorted(tasks_with_id, key=prioritize_today)
        typer.echo(tabulate(sorted_tasks, headers=headers, tablefmt="pretty"))

@app.command()
def today():
    """
    List add tasks added today.
    """
    config = load_config()
    with open(config["todo_file"], "r") as f:
        tasks = [line.strip().split(",") for line in f.readlines()]
    
    if not tasks:
        print("[bold green]No tasks due today[/bold green]")
    else:
        today = datetime.date.today().strftime("%Y-%m-%d")
        headers = ["ID", "Task", "Priority", "Estimated Completion Minutes", "Date"]
        tasks_with_id = [[str(i+1)] + task for i, task in enumerate(tasks) if task[3] == today]
        if not tasks_with_id:
            print("[bold green]No tasks due today[/bold green]")
        else:
            sorted_tasks = sorted(tasks_with_id, key=lambda x: (x[2], x[3]))
            typer.echo(tabulate(sorted_tasks, headers=headers, tablefmt="pretty"))

@app.command()
def delete(task_id: Annotated[int, typer.Argument(help="The ID of the task to delete")]):
    """
    Delete a task from the todo file.
    """
    config = load_config()
    with open(config["todo_file"], "r") as f:
        tasks = f.readlines()
        
    if task_id < 1 or task_id > len(tasks):
        print("[bold red]Task ID not found[/bold red]")
        raise typer.Exit(code=1)
    
    delete_item = tasks[task_id - 1]
    tasks.remove(delete_item)
        
    with open(config["todo_file"], "w") as f:
        f.writelines(tasks)
        
    print(f"[bold red]Task deleted: {delete_item.split(',')[0]}[/bold red]")
    
@app.command()
def do(task_id: Annotated[int, typer.Argument(help="The ID of the task to mark as done")]):
    """
    Mark a task as done and remove it from the todo file.
    """
    config = load_config()
    with open(config["todo_file"], "r") as f:
        tasks = f.readlines()
        
    if task_id < 1 or task_id > len(tasks):
        print("[bold red]Task ID not found[/bold red]")
        raise typer.Exit(code=1)
    
    done_item = tasks[task_id - 1]
    tasks.remove(done_item)
    
    try:
        with open(config["done_file"], "a") as f:
            f.write(done_item)
        
        with open(config["todo_file"], "w") as f:
            f.writelines(tasks)
        
        print(f"[bold green]Task done: {done_item.split(',')[0]}[/bold green]")
    except Exception as e:
        print(f"[bold red]Error marking task as done: {e}[/bold red]")
        raise typer.Exit(code=1)

@app.command()
def edit(task_id: Annotated[int, typer.Argument(help="The ID of the task to edit")], task_name: Annotated[str, typer.Argument(help="The new name of the task")], priority: Annotated[Optional[str], typer.Argument(help="Priority of the task (A-Z)")] = None, estimated_completion_minutes: Annotated[Optional[str], typer.Argument(help="Estimated completion minutes")] = None):
    """
    Edit a task in the todo file.
    """
    config = load_config()
    with open(config["todo_file"], "r") as f:
        tasks = f.readlines()
        
    if task_id < 1 or task_id > len(tasks):
        print("[bold red]Task ID not found[/bold red]")
        raise typer.Exit(code=1)
    
    task = Task(task_name, priority, estimated_completion_minutes)
    task_details = f"{task.name},{task.priority},{task.est_min},{task.date}\n"
    tasks[task_id - 1] = task_details
    
    with open(config["todo_file"], "w") as f:
        f.writelines(tasks)
        
    print(f"[bold green]Task edited: {task_name}[/bold green]")
