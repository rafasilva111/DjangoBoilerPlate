
import logging
from os import makedirs,path,rename,listdir, remove
from celery import shared_task
from django.utils import timezone
from django.conf import settings

# Description: This file contains all the functions used in the project
import json
import time
import uuid
from datetime import datetime

import shutil

import firebase_admin
import requests
from firebase_admin import credentials, initialize_app, storage
from peewee import SqliteDatabase

from apps.common.constants import FIREBASE_STORAGE_BASE_BUCKET


""" Main Datbase """





def start_firebase():
    cred = credentials.Certificate("keys/pfm-firebase-sdk.json")
    initialize_app(cred, {
        'storageBucket': FIREBASE_STORAGE_BASE_BUCKET
    })


def close_firebase():
    firebase_admin.delete_app(firebase_admin.get_app())


def send_image_to_firebase(image_destination, image_source):
    # Add your own directory path and file name
    blob = storage.bucket().blob(image_destination)

    # Check if the file exists
    if not blob.exists():
        # Open the file in read mode
        with open(image_source, 'rb') as my_file:
            blob.upload_from_file(my_file)



def generate_image_name():
    # Generate a unique image name using a timestamp and random component
    timestamp = int(time.time())
    random_suffix = str(uuid.uuid4().hex[:6])  # Generate a 6-character random string
    image_name = f"image_{timestamp}_{random_suffix}.jpg"
    return image_name

    
    
def delete_task_logs(task):
    
    if task.log_path:
        directory_path = path.dirname(task.log_path)
        
        if path.exists(directory_path):
            shutil.rmtree(directory_path)

def delete_task_database(task):

    try:

        if task.sql_file:
            remove(task.sql_file)
    except FileNotFoundError:
        pass
    
    
    
def configure_logging(log_folder):
    
    # Create the log folder
    makedirs(log_folder , exist_ok=True)
    
    # Define log filenames with the creation date
    date = timezone.now().strftime("%d_%m_%Y__%H_%M")
    info_log_filename = f'{log_folder}/info__{date}.log'
    error_log_filename = f'{log_folder}/errors__{date}.log'
    
    # Create different handlers for different log levels
    info_handler = logging.FileHandler(info_log_filename)
    info_handler.setLevel(logging.INFO)

    error_handler = logging.FileHandler(error_log_filename)
    error_handler.setLevel(logging.ERROR)

    # Define the logging format and add it to handlers
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Configure the logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Add handlers to the logger
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    
    return logger, info_log_filename

def configure_job_logging(job):
    
    log_folder = settings.JOBS_LOG_DIR / str( job.id)
    
    # Configure the logging
    logger, log_info_path = configure_logging(log_folder)

    return logger, log_info_path

def configure_task_logging(task):
    
    # Define the log folder

    
    log_folder = settings.TASKS_LOG_DIR / str( task.id)
    
    # Configure the logging
    logger, log_info_path = configure_logging(log_folder)

    return logger, log_info_path
    