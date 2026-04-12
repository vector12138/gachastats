"""Test runner script for GachaStats"""
import subprocess
import sys


def run_tests():
    """运行所有测试文件"""
    test_files = [
        "backend/tests/test_accounts_new.py",
        "backend/tests/test_main.py",
        "backend/tests/test_utils.py"
    ]

    print("正在运行GachaStats后端测试...\n")

    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"运行测试文件: {test_file}")
        print(f"{'='*60}\n")

        # 运行测试
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            print(f"\n⚠️  {test_file} 测试中遇到问题，继续运行其他测试...")
            continue

    print(f"\n{'='*60}")
    print("测试运行完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_tests()