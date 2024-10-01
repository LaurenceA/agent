
import pytest
from strange_loop_agent.check_command import check_command

def test_print_command():
    command = "cat filename.txt"
    result = check_command(command)
    assert isinstance(result, dict)
    assert result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert not result["trying_to_write"]
    assert not result["trying_to_modify"]

def test_write_command():
    command = "echo 'Hello, World!' > output.txt"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert result["trying_to_write"]
    assert not result["trying_to_modify"]

def test_modify_command():
    command = "sed -i '' 's/original/replacement/' file.txt"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert not result["trying_to_write"]
    assert result["trying_to_modify"]

def test_ambiguous_command():
    command = "grep 'pattern' file.txt > results.txt"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert result["trying_to_write"]
    assert not result["trying_to_modify"]

def test_other_command():
    command = "other_command"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert not result["trying_to_write"]
    assert not result["trying_to_modify"]

def test_ls_command():
    command = "ls -l dirname"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert result["trying_to_print_directory"]
    assert not result["trying_to_create_empty_file"]
    assert not result["trying_to_write"]
    assert not result["trying_to_modify"]

def test_touch_command():
    command = "touch newfile"
    result = check_command(command)
    assert isinstance(result, dict)
    assert not result["trying_to_print_file"]
    assert not result["trying_to_print_directory"]
    assert result["trying_to_create_empty_file"]
    assert not result["trying_to_write"]
    assert not result["trying_to_modify"]
