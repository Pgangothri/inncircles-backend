import os
import sys
import subprocess
import platform
from typing import Union, List

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.config_loader import load_config
from src.utils.xml_formatter import xml_wrap
from src.utils.logging_config import logger  # ✅ Import logger

class ShellTool:
    def __init__(self):
        self.tool_name = "shell_tool"
        self.config = load_config("tools_config.yaml")["tools"]["shell_tool"]
        self.is_windows = platform.system().lower() == "windows"
        self.default_workdir = self.config.get("default_workdir", ".")
        self.timeout = self.config.get("timeout_seconds", 20)

        logger.info("[ShellTool] Initialized | OS: %s | Workdir: %s | Timeout: %ds",
                    platform.system(), self.default_workdir, self.timeout)

    def execute(self, command: Union[str, List[str]]) -> str:
        if isinstance(command, str):
            command = command.strip()

        logger.info("[ShellTool] Executing command: %s", command)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=self.is_windows,
                cwd=self.default_workdir
            )

            if result.returncode == 0:
                logger.info("[ShellTool] Command succeeded: %s", command)
                logger.debug("[ShellTool] Output: %s", result.stdout.strip())
                return xml_wrap(
                    task_id="task_shell_001",
                    status="completed",
                    current_step="shell_tool::execute_command",
                    tools_used=[{
                        "name": self.tool_name,
                        "status": "active",
                        "action": command,
                        "output": "Command executed successfully"
                    }],
                    reasoning={
                        "thought": "Ran the shell command in the configured working directory.",
                        "next_action": "Pass result to downstream logic or summarize."
                    },
                    result={
                        "success": True,
                        "data": result.stdout.strip(),
                        "errors": ""
                    }
                )
            else:
                logger.warning("[ShellTool] Command failed: %s | Exit code: %d", command, result.returncode)
                logger.debug("[ShellTool] Stderr: %s", result.stderr.strip())
                return xml_wrap(
                    task_id="task_shell_001",
                    status="failed",
                    current_step="shell_tool::execute_command",
                    tools_used=[{
                        "name": self.tool_name,
                        "status": "failed",
                        "action": command,
                        "output": result.stderr.strip()
                    }],
                    reasoning={
                        "thought": "Command returned non-zero exit code.",
                        "next_action": "Check for syntax or permission issues."
                    },
                    result={
                        "success": False,
                        "data": "",
                        "errors": result.stderr.strip()
                    }
                )

        except subprocess.TimeoutExpired:
            logger.error("[ShellTool] Command timed out after %ds: %s", self.timeout, command)
            return xml_wrap(
                task_id="task_shell_001",
                status="failed",
                current_step="shell_tool::execute_command",
                tools_used=[{
                    "name": self.tool_name,
                    "status": "failed",
                    "action": command,
                    "output": "Timeout"
                }],
                reasoning={
                    "thought": "Command execution took too long.",
                    "next_action": "Consider increasing timeout or optimizing command."
                },
                result={
                    "success": False,
                    "data": "",
                    "errors": "Command timed out."
                }
            )

        except FileNotFoundError:
            logger.error("[ShellTool] Command not found: %s", command)
            return xml_wrap(
                task_id="task_shell_001",
                status="failed",
                current_step="shell_tool::execute_command",
                tools_used=[{
                    "name": self.tool_name,
                    "status": "failed",
                    "action": command,
                    "output": "Command not found"
                }],
                reasoning={
                    "thought": "Likely invalid command or typo.",
                    "next_action": "Suggest correcting the command."
                },
                result={
                    "success": False,
                    "data": "",
                    "errors": f"Command not found: {command}"
                }
            )

        except Exception as e:
            logger.exception("[ShellTool] Unexpected error executing command: %s", command)
            return xml_wrap(
                task_id="task_shell_001",
                status="failed",
                current_step="shell_tool::execute_command",
                tools_used=[{
                    "name": self.tool_name,
                    "status": "failed",
                    "action": command,
                    "output": str(e)
                }],
                reasoning={
                    "thought": "Unexpected error occurred.",
                    "next_action": "Log for debugging and alert developer."
                },
                result={
                    "success": False,
                    "data": "",
                    "errors": str(e)
                }
            )


