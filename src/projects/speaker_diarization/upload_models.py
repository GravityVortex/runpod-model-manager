#!/usr/bin/env python3
"""上传 speaker-diarization 模型到 S3"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.project_uploader import ProjectUploader
from src.projects.speaker_diarization.config import SpeakerDiarizationProject

if __name__ == '__main__':
    exit(ProjectUploader.main_cli(SpeakerDiarizationProject()))

