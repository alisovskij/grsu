import os

from fastapi import UploadFile


async def save_upload_file(
        file: UploadFile,
        directory: str,
        filename: str
) -> str:

    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return file_path