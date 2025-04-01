import logging
import os
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import time

from fastapi import APIRouter, Depends, File as FastAPIFile, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.files import (
    FileForm,
    FileModel,
    FileModelResponse,
    Files,
    File,
)
from open_webui.internal.db import get_db
from open_webui.routers.retrieval import ProcessFileForm, process_file
from open_webui.routers.audio import transcribe
from open_webui.storage.provider import Storage
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import BaseModel

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


router = APIRouter()

# Define FilenameForm
class FilenameForm(BaseModel):
    filename: str

############################
# Upload File
############################

@router.post("/{id}/filename/update")
async def update_file_filename_by_id(
    id: str, form_data: FilenameForm, user=Depends(get_verified_user)
):
    try:
        file = Files.get_file_by_id(id=id)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.FILE_NOT_FOUND,
            )

        # Update file metadata
        file_meta = file.meta or {}
        file_meta["name"] = form_data.filename
        
        # Update filename in database
        Files.update_file_metadata_by_id(id=id, meta=file_meta)
        
        # Also update the filename field
        with get_db() as db:
            try:
                file_obj = db.query(File).filter_by(id=id).first()
                file_obj.filename = form_data.filename
                file_obj.updated_at = int(time.time())
                db.commit()
                updated_file = Files.get_file_by_id(id=id)
                return updated_file
            except Exception as e:
                log.exception(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ERROR_MESSAGES.FAILED_TO_UPDATE_FILE,
                )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
