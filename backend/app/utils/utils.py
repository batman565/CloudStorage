from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.modules import File, Folder
from app.modules.pydanticmodels import FileInfo, FolderContentResponse, FolderInfo
import aiofiles


async def get_files_and_folders(user_id: int, folder_id: int, folder_name: str, db: AsyncSession, folder_parent_id: int = None):
    result_folders = await db.execute(select(Folder).where(
        Folder.parent_folder_id == folder_id,
        Folder.user_id == user_id
    ))
    folders = result_folders.scalars().all()

    result_files = await db.execute(select(File).where(
        File.ownerid == user_id,
        File.folderid == folder_id
    ))
    files = result_files.scalars().all()

    return FolderContentResponse(current_folder=FolderInfo(id=folder_id, name=folder_name),
                                 folder_parent_id=folder_parent_id,
                                subfolders=[FolderInfo(id=folder.id, name=folder.name) for folder in folders],
                                files=[FileInfo(id=file.id, name=file.name, weight=file.weight) for file in files])

