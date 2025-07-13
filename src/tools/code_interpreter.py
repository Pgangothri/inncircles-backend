import os, sys
import time
import dotenv

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.xml_formatter import xml_wrap
from src.tools.base import Tools

try:
    from daytona import Daytona, DaytonaConfig, CreateSandboxFromSnapshotParams
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

dotenv.load_dotenv()

class CodeInterpreterTool(Tools):
    """
    Tool to execute arbitrary code (e.g., Python) in a Daytona sandbox.
    """

    def __init__(self):
        super().__init__()
        self.tag = "code_interpreter"
        self.api_key = os.getenv("DAYTONA_API_KEY")
        if not SDK_AVAILABLE or not self.api_key:
            self.daytona = None
            return

        config = DaytonaConfig(api_key=self.api_key)
        self.daytona = Daytona(config)

    def create_sandbox(self, language="python"):
        params = CreateSandboxFromSnapshotParams(
            name=f"code-interpreter-{int(time.time())}",
            language=language
        )
        return self.daytona.create(params)

    def execute_code(self, code, language="python"):
        if not SDK_AVAILABLE or not self.daytona:
            return "[error] Daytona SDK not initialized."

        try:
            sandbox = self.create_sandbox(language=language)
            result = sandbox.process.code_run(code)

            return xml_wrap(
                task_id="code_interpreter",
                status="completed",
                current_step="run_code",
                tools_used=[{
                    "name": self.tag,
                    "status": "executed",
                    "action": "code_run",
                    "output": result.result
                }],
                reasoning={"thought": "Executed user code in sandbox", "next_action": "return result"},
                result={"success": "true", "data": result.result, "errors": ""}
            )

        except Exception as e:
            return xml_wrap(
                task_id="code_interpreter",
                status="failed",
                current_step="run_code",
                tools_used=[{
                    "name": self.tag,
                    "status": "error",
                    "action": "code_run",
                    "output": str(e)
                }],
                reasoning={"thought": "Failed to execute code", "next_action": "abort"},
                result={"success": "false", "data": "", "errors": str(e)}
            )

    def execute(self, code, safety=True, **kwargs):
        """
        Unified interface compatible with tool runner.
        :param code: str - Python code to run
        :param safety: bool - Reserved for sandbox toggle (not used yet)
        """
        return self.execute_code(code)
