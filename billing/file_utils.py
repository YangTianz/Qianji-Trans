import datetime
import os
import traceback

from typing import Callable


def is_target_file(file_name: str) -> bool:
    return True


def ensure_dir_exist(path: str) -> None:
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except FileNotFoundError:
            raise


def scan_and_move(
    source_dir: str,
    destination_dir: str,
    file_filter: Callable = is_target_file,
    prefix: str = "",
    postfix: str = "",
) -> dict[str, bytes]:
    try:
        # 扫描指定目录
        files = os.listdir(source_dir)
        valid_files = list(filter(file_filter, files))

        file_contents = {}
        # 加载文件到内存
        for file_name in valid_files:
            file_path = os.path.join(source_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    file_contents[file_name] = file.read()

        # 将文件移动到另一个目录
        for file_name, content in file_contents.items():
            base_name, ext = os.path.splitext(file_name)
            file_name = f"{prefix}{base_name}{postfix}{ext}"
            destination_path = os.path.join(destination_dir, file_name)
            with open(destination_path, "wb") as destination_file:
                destination_file.write(content)

        # 删除原始目录下的文件
        for file_name in valid_files:
            file_path = os.path.join(source_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return file_contents
    except Exception:
        print(datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
        traceback.print_exc()
        return {}
