import pytest
from typer.testing import CliRunner
import os
from todo.main import app
import shutil
import json

runner =CliRunner()

@pytest.fixture(scope="function")
def setup_todo():
    root_dir = os.path.expanduser("~")
    os.mkdir(os.path.join(root_dir, ".todo-test"))
    
    config = {
        "todo_dir": os.path.join(root_dir, ".todo-test"),
        "todo_file": os.path.join(root_dir, ".todo-test", "todo-test.txt"),
        "done_file": os.path.join(root_dir, ".todo-test", "done-test.txt")
    }
    
    with open(".todo_config.json", "w") as f:
        f.write(json.dumps(config))
        
    with open(config["todo_file"], "w"):
        pass
    
    with open(config["done_file"], "w"):
        pass
    
    yield
    
    shutil.rmtree(os.path.expanduser("~/.todo-test"))

@pytest.fixture(scope="function")
def setup_add_multiple_todos(setup_todo):
    root_dir = os.path.expanduser("~")
    with open(os.path.join(root_dir, ".todo-test", "todo-test.txt"), "w") as f:
        f.write("Buy milk,A,30,2024-02-24\n")
        f.write("Buy eggs,C,15,2024-02-23\n")
        f.write("Buy bread,A,45,2024-02-24\n")

def test_init():
    todo_directory = os.path.expanduser("~/.todo")
    try:
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert os.path.exists(".todo_config.json")
        assert os.path.exists(todo_directory)
        assert os.path.exists(os.path.join(todo_directory, "todo.txt"))
        assert os.path.exists(os.path.join(todo_directory, "done.txt"))
    finally:
        if os.path.exists(".todo_config.json"):
            os.remove(".todo_config.json")
        if os.path.exists(todo_directory):
            shutil.rmtree(todo_directory)

def test_init_with_custom_name():
    todo_directory = os.path.expanduser("~/.todo-test")
    try:
        result = runner.invoke(app, ["init", ".todo-test", "todo-test.txt", "done-test.txt"])
        assert result.exit_code == 0
        assert os.path.exists(".todo_config.json")
        assert os.path.exists(os.path.expanduser("~/.todo-test"))
        assert os.path.exists(os.path.join(os.path.expanduser("~/.todo-test"), "todo-test.txt"))
        assert os.path.exists(os.path.join(os.path.expanduser("~/.todo-test"), "done-test.txt"))
    finally:
        if os.path.exists(".todo_config.json"):
            os.remove(".todo_config.json")
        if os.path.exists(todo_directory):
            shutil.rmtree(todo_directory)

def test_init_with_invalid_todo_file():
    result = runner.invoke(app, ["init", ".todo-test", "todo", "done-test.txt"])
    assert result.exit_code != 0
    assert "todo_file and done_file must ends with .txt" in result.stdout

def test_add(setup_todo):
    result = runner.invoke(app, ["add", "Buy milk"])
    assert result.exit_code == 0
    assert "Buy milk" in result.stdout
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" in content

def test_add_with_optional_arguments(setup_todo):
    result = runner.invoke(app, ["add", "Buy milk", "A", "30"])
    assert result.exit_code == 0
    assert "Buy milk" in result.stdout
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk,A,30,2024-02-24" in content

def test_add_with_invalid_priority(setup_todo):
    result = runner.invoke(app, ["add", "Buy milk", "A1"])
    assert result.exit_code != 0
    assert "Priority must be a single alphabet character (A-Z)" in result.stdout
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" not in content

def test_add_with_invalid_est_min(setup_todo):
    result = runner.invoke(app, ["add", "Buy milk", "A", "thirty"])
    assert result.exit_code != 0
    assert "Estimated completion minutes must be a positive integer" in result.stdout
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" not in content

def test_add_two_same_priorities(setup_todo):
    result = runner.invoke(app, ["add", "Buy milk", "A", "30"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["add", "Buy eggs", "A", "15"])
    assert result.exit_code == 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk,A,30,2024-02-24" in content
        assert "Buy eggs,A,15,2024-02-24" in content

def test_list(setup_add_multiple_todos):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0

def test_today(setup_add_multiple_todos):
    result = runner.invoke(app, ["today"])
    assert result.exit_code == 0
    
def test_delete(setup_add_multiple_todos):
    result = runner.invoke(app, ["delete", "1"])
    assert result.exit_code == 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" not in content

def test_delete_with_invalid_index(setup_add_multiple_todos):
    result = runner.invoke(app, ["delete", "4"])
    assert result.exit_code != 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" in content

def test_done(setup_add_multiple_todos):
    result = runner.invoke(app, ["do", "1"])
    assert result.exit_code == 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk,A,30,2024-02-24" not in content
    with open(os.path.expanduser("~/.todo-test/done-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk,A,30,2024-02-24" in content

def test_done_with_invalid_index(setup_add_multiple_todos):
    result = runner.invoke(app, ["do", "4"])
    assert result.exit_code != 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" in content
    with open(os.path.expanduser("~/.todo-test/done-test.txt"), "r") as f:
        content = f.read()
        assert "Buy milk" not in content

def test_edit(setup_add_multiple_todos):
    result = runner.invoke(app, ["edit", "1", "Buy water, A, 30, 2024-02-24"])
    assert result.exit_code == 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy water, A, 30, 2024-02-24" in content

def test_edit_with_invalid_index(setup_add_multiple_todos):
    result = runner.invoke(app, ["edit", "4", "Buy water, A, 30, 2024-02-24"])
    assert result.exit_code != 0
    with open(os.path.expanduser("~/.todo-test/todo-test.txt"), "r") as f:
        content = f.read()
        assert "Buy water,A,30,2024-02-24" not in content
