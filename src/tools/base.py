
"""
define a generic tool class, any tool can be used by the agent.

A tool can be used by deepseek like so:
```<tool name>
<code or query to execute>
```

For example:
```python
print("Hello world")
```
This is then executed by the tool with its own class implementation of execute().
A tool is not just for code tool but also API, internet, etc..
"""

import sys
import os
import configparser
from abc import abstractmethod

sys.path.append('..')

class Tools():
    """
    Abstract class for all tools.
    """
    def __init__(self):
        self.tag = "undefined"
        self.api_key = None
        self.client = None
        self.messages = []
        self.config = configparser.ConfigParser()
        self.current_dir = self.create_work_dir()
        self.excutable_blocks_found = False
    
    def check_config_dir_validity(self):
        """
        Check if the config directory is valid.
        """
        path = self.config['MAIN']['work_dir']
        if path == "":
            print("WARNING: Work directory not set in config.ini")
            return False
        if path.lower() == "none":
            print("WARNING: Work directory set to none in config.ini")
            return False
        if not os.path.exists(path):
            print(f"WARNING: Work directory {path} does not exist")
            return False
        return True
    
    def config_exists(self):
        """
        Check if the config file exists.
        """
        return os.path.exists('./config.ini')

    def create_work_dir(self):
        """
        Create the work directory if it does not exist.
        """
        default_path = os.path.dirname(os.getcwd())
        if self.config_exists():
            self.config.read('./config.ini')
            config_path = self.config['MAIN']['work_dir']
            dir_path = default_path if not self.check_config_dir_validity() else config_path
        else:
            dir_path = default_path
        return dir_path

    @abstractmethod
    def execute(self, blocks:str, safety:bool) -> str:
        """
        Abstract method that must be implemented by child classes to execute the tool's functionality.
        Args:
            blocks (List[str]): The codes or queries blocks to execute
            safety (bool): Whenever human intervention is required
        Returns:
            str: The output/result from executing the tool
        """
        pass

    @abstractmethod
    def execution_failure_check(self, output:str) -> bool:
        """
        Abstract method that must be implemented by child classes to check if tool execution failed.
        Args:
            output (str): The output string from the tool execution to analyze
        Returns:
            bool: True if execution failed, False if successful
        """
        pass

    @abstractmethod
    def interpreter_feedback(self, output:str) -> str:
        """
        Abstract method that must be implemented by child classes to provide feedback to the AI from the tool.
        Args:
            output (str): The output string from the tool execution to analyze
        Returns:
            str: The feedback message to the AI
        """
        pass

    def save_block(self, blocks:str, save_path:str) -> None:
        """
        Save code or query blocks to a file at the specified path.
        Creates the directory path if it doesn't exist.
        Args:
            blocks (List[str]): List of code/query blocks to save
            save_path (str): File path where blocks should be saved
        """
        if save_path is None:
            return
        save_path_dir = os.path.dirname(save_path)
        save_path_file = os.path.basename(save_path)
        directory = os.path.join(self.current_dir, save_path_dir)
        if directory and not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory)
        for block in blocks:
            print(f"Saving code block to: {save_path}")
            with open(os.path.join(directory, save_path_file), 'w') as f:
                f.write(block)
    
    def found_executable_blocks(self):
        """
        Check if executable blocks were found.
        """
        tmp = self.excutable_blocks_found
        self.excutable_blocks_found = False
        return tmp

    def load_exec_block(self, llm_text: str) -> tuple[list[str], str | None]:
        """
        Extract code/query blocks from LLM-generated text and process them for execution.
        This method parses the text looking for code blocks marked with the tool's tag (e.g. ```python).
        Args:
            llm_text (str): The raw text containing code blocks from the LLM
        Returns:
            tuple[list[str], str | None]: A tuple containing:
                - List of extracted and processed code blocks
                - The path the code blocks was saved to
        """
        assert self.tag != "undefined", "Tag not defined"
        start_tag = f'```{self.tag}' 
        end_tag = '```'
        code_blocks = []
        start_index = 0
        save_path = None

        if start_tag not in llm_text:
            return None, None

        while True:
            start_pos = llm_text.find(start_tag, start_index)
            if start_pos == -1:
                break

            line_start = llm_text.rfind('\n', 0, start_pos) + 1
            if line_start == 0:
                line_start = 0
            leading_whitespace = llm_text[line_start:start_pos]

            end_pos = llm_text.find(end_tag, start_pos + len(start_tag))
            if end_pos == -1:
                break
            content = llm_text[start_pos + len(start_tag):end_pos]
            lines = content.split('\n')
            if leading_whitespace:
                processed_lines = []
                for line in lines:
                    if line.startswith(leading_whitespace):
                        processed_lines.append(line[len(leading_whitespace):])
                    else:
                        processed_lines.append(line)
                content = '\n'.join(processed_lines)

            if ':' in content.split('\n')[0]:
                save_path = content.split('\n')[0].split(':')[1]
                content = content[content.find('\n')+1:]
            self.excutable_blocks_found = True
            code_blocks.append(content)
            start_index = end_pos + len(end_tag)
        return code_blocks, save_path

if __name__ == "__main__":
    tool = Tools()
    tool.tag = "python"
    rt = tool.load_exec_block("""
Got it, let me show you the Python files in the current directory using Python:

```python
import os

for file in os.listdir():
    if file.endswith('.py'):
        print(file)
```
    """)
    print(rt)