import subprocess

class AndroidDeviceHandler:
    def _run_adb_command(self, command: str):
        result = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ADB command failed: {result.stderr}")
        return result.stdout.strip()

    def get_resolution(self):
        output = self._run_adb_command("shell wm size")
        return output.split(": ")[1]
    
    def clear_app_data(self, package_name: str):
        self._run_adb_command(f"shell pm clear {package_name}")