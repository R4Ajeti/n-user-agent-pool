import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from core import ChromeUserAgentPoolService


class PackageImportTest(unittest.TestCase):
    def testSourceCoreNamespaceImportsService(self) -> None:
        self.assertEqual(
            "ChromeUserAgentPoolService",
            ChromeUserAgentPoolService.__name__,
        )

    def testWheelExportsCoreNamespaceOnly(self) -> None:
        repoPath = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tempDirStr:
            tempPath = Path(tempDirStr)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    str(repoPath),
                    "-w",
                    str(tempPath),
                    "--no-deps",
                ],
                check=True,
                cwd=tempPath,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            wheelPath = next(tempPath.glob("*.whl"))

            with zipfile.ZipFile(wheelPath) as wheelFile:
                topLevelFileName = next(
                    fileName
                    for fileName in wheelFile.namelist()
                    if fileName.endswith(".dist-info/top_level.txt")
                )
                topLevelTextStr = wheelFile.read(topLevelFileName).decode("utf-8").strip()
                topLevelNameSet = set(topLevelTextStr.splitlines())
                self.assertEqual({"core"}, topLevelNameSet)
                self.assertTrue(
                    any(fileName.startswith("core/") for fileName in wheelFile.namelist())
                )

            importResult = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys; "
                        f"sys.path.insert(0, {str(wheelPath)!r}); "
                        "from core import ChromeUserAgentPoolService; "
                        "print(ChromeUserAgentPoolService.__name__)"
                    ),
                ],
                check=True,
                cwd=tempPath,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("ChromeUserAgentPoolService", importResult.stdout.strip())


if __name__ == "__main__":
    unittest.main()
