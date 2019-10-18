#!/bin/python3.7

import pandas
from googleapiclient import (
    discovery,
    http,
)  # google-api-python-client
from google_auth_oauthlib import get_user_credentials
from os import path, getcwd, getpid, system
from re import sub
from io import FileIO
from slugify import slugify
from sys import exit, stderr
import json
import logging
from email.mime.text import MIMEText
import base64
import unicodedata
from sys import excepthook
from time import sleep
import daemon


###############################
#### FUNCTIONS DEFINITIONS ####
###############################


def get_proper_mimetype_and_filename(
    Mod_time: str, name: str, mimetype: str
):
    # Here we change names and such, so that they are of correct format for file name. slugify is amazing at this
    filenamed_name = slugify(name)
    Mod_time_proper = sub(":|\.", "_", Mod_time)

    # Here we establish which files should be saved on disc using which format, based on their mimetype. This needs to be inside the function, cause it establishes two
    mimetype_to_export_file_as = "text/plain"
    extension_for_exported_file = ".txt"

    if (
        mimetype
        == "application/vnd.google-apps.spreadsheet"
    ):
        mimetype_to_export_file_as = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        extension_for_exported_file = ".xlsx"
    elif mimetype == "application/vnd.google-apps.document":
        mimetype_to_export_file_as = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        extension_for_exported_file = ".docx"
    elif (
        mimetype
        == "application/vnd.google-apps.presentation"
    ):
        mimetype_to_export_file_as = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        extension_for_exported_file = ".pptx"

    return {
        "proper_mimetype": mimetype_to_export_file_as,
        "proper_filename": f"{filenamed_name}_{Mod_time_proper}{extension_for_exported_file}",
    }


# The parameters are the data you get from google drive
def download_the_file(
    Id: str, Mod_time: str, name: str, mimetype: str, drive
):

    proper_mimetype_and_filename = get_proper_mimetype_and_filename(
        Mod_time=Mod_time, name=name, mimetype=mimetype
    )

    # I am not sure why this workflow looks the way it looks. Future me - your on your own and you know as much as I do
    try:
        request = drive.files().export(
            fileId=Id,
            mimeType=proper_mimetype_and_filename[
                "proper_mimetype"
            ],
        )
    except:
        logging.error("Creating export failed")
        raise Exception("Creating export failed")

    try:
        fh = FileIO(
            proper_mimetype_and_filename["proper_filename"],
            "wb",
        )
    except:
        logging.error("Creating file on a disc failed")
        raise Exception("Creating file on a disc failed")

    downloader = http.MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        try:
            status, done = downloader.next_chunk()
        except:
            logging.error(
                "downloading piece of a file failed"
            )
            raise Exception("xxx")

        print(
            f"Downloading: {proper_mimetype_and_filename['proper_filename']}"
        )


# This function compares old andnew time
def download_the_file_with_changed_modification_time(
    Id: str,
    Mod_time_old: str,
    Mod_time_new: str,
    name: str,
    mimetype: str,
    drive,
):
    if Mod_time_old != Mod_time_new:
        download_the_file(
            Id=Id,
            Mod_time=Mod_time_new,
            name=name,
            mimetype=mimetype,
            drive=drive,
        )


def set_id_and_secret(secret_file_name_: str):
    if path.isfile(secret_file_name_) == True:
        with open(secret_file_name_) as json_file:
            json_file_loaded = json.load(json_file)
            return {
                "client_id": json_file_loaded["installed"][
                    "client_id"
                ],
                "client_secret": json_file_loaded[
                    "installed"
                ]["client_secret"],
            }
    else:
        logging.error(
            f"No secret file found. It needs to be inside the same folder as the script and should be named: {secret_file_name_}"
        )
        raise Exception("xxx")


def send_message(service, user_id, message):
    message = (
        service.users()
        .messages()
        .send(userId=user_id, body=message)
        .execute()
    )
    return message


def create_message(
    sender: str = "igab.pas@gmail.com",
    to: str = "adrianstankiewicz85@gmail.com, igab.pas@gmail.com",
    subject: str = "GDocs_backuper reporting",
    message_text: str = "",
):
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    # This is what need to be done to send mail via google api. Im human trash to them. MIMEText -> string -> bytes -> string(??). Cool.
    bytes_message = base64.urlsafe_b64encode(
        message.as_string().encode()
    )
    bytes_message_decoded = bytes_message.decode()
    return {"raw": bytes_message_decoded}


def get_user_credentials_with_try(
    scopes_, client_id_, client_secret_
):
    print("Getting user credentials...")
    try:
        creds_ = get_user_credentials(
            scopes_, client_id_, client_secret_
        )
    except:
        ## Cannot mail this error to myself, because I dont have access to mail yet...
        logging.error("Geting user credentials failed")
        raise Exception("Geting user credentials failed")
    print("Got user credentials\n")
    return creds_


# execute() sends the request to google. The things before it, are methods for this specific resource type. The "get" is a python dictionary method. Not sure how Resoucre objects translates to python dictionary though. Dont understand get() arguments either. list() needs to explicitly state needed fields, or it returns only small set of them. "*" returns all fields. You can return only fields You want, but syntax of this query was written by some cunt, and its a waste of my time to learn it.
def get_list_of_files(drive_, mail_):
    print("Listing files...")
    try:
        files_ = (
            drive_.files()
            .list(fields="*")
            .execute()
            .get("files", [])
        )
    except:
        logging.error("Getting list of files failed")
        if mail_ != None:
            did_u_sent_it = send_message(
                service=mail_,
                user_id="me",
                message=create_message(
                    message_text="Error occured in GDocs_backuper: accessing list of files. Script is down, do something about it!"
                ),
            )
        raise Exception("Getting list of files failed")
    print("Files listed\n")
    return files_


def build_service_image(
    serviceName_: str,
    version_: str,
    credentials_,
    mail_=None,
):
    print(f"Building {serviceName_}")
    try:
        service_ = discovery.build(
            serviceName=serviceName_,
            version=version_,
            credentials=credentials_,
            cache_discovery=False,
        )
    except:
        logging.error(
            f"Building a {serviceName_} image failed"
        )
        if mail_ != None:
            did_u_sent_it = send_message(
                service=mail_,
                user_id="me",
                message=create_message(
                    message_text=f"Error occured in GDocs_backuper: building a {serviceName_} image. Script is down, do something about it!"
                ),
            )
        raise Exception(
            f"Building a {serviceName_} image failed"
        )
    print(f"{serviceName_} built\n")
    return service_


def write_new_files_of_interest_file(
    new_files_of_interest_, mail_=None
):
    print("Writing files_of_interest.csv file")
    try:
        new_files_of_interest_.to_csv(
            "files_of_interest.csv"
        )
    except:
        logging.error("Creating new file list failed")
        if mail_ != None:
            did_u_sent_it = send_message(
                service=mail_,
                user_id="me",
                message=create_message(
                    message_text=f"Error occured in GDocs_backuper: writing files_of_interest.csv file. Script is down, do something about it!"
                ),
            )
        raise Exception("Creating new file list failed")
    print("files_of_interest.csv file written\n")


def wait_report_back_and_loop(
    how_frequently_to_check_for_updates_: int,
    loop_nb_: int,
    mail_=None,
):
    sleep(how_frequently_to_check_for_updates_)
    logging.error(
        f"GDocs_backuper is running (PID: {getpid()}, loop number: {loop_nb_})"
    )
    if loop_nb_ % 10 == 0:
        when_to_report_back_activity = (
            how_frequently_to_check_for_updates_ * 10
        ) / 3600
        did_u_sent_it = send_message(
            service=mail_,
            user_id="me",
            message=create_message(
                message_text=f"The GDocs_backuper is working fine. I will be reporting back in {when_to_report_back_activity} hours"
            ),
        )
    return loop_nb_ + 1


# Check what it does when internets goes down - it seems ok. Check keyboard interrupt!
def excepthook_for_GDocs_loop(mail_=None):
    logging.exception(f"GDocs_backuper failed during loop!")
    if mail_ != None:
        did_u_sent_it = send_message(
            service=mail_,
            user_id="me",
            message=create_message(
                message_text="GDocs_backuper failed during loop!"
            ),
        )
    raise Exception(f"GDocs_backuper failed during loop!")


###############################
#### FUNCTIONS DEFINITIONS ####
###############################


###############################
######### CONSTANTS ###########
###############################

how_frequently_to_check_for_updates = 3
scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
]
secret_file_name = "client_secret.json"

###############################
######### CONSTANTS ###########
###############################


def main():
    # When initianting logger like this, we have access to handler (~pointer) of (to) its file
    fh = logging.FileHandler("GDocs_backuper.log")
    logging.basicConfig(
        format="%(asctime)s - %(message)s", handlers=[fh]
    )
    logging.error(f"GDocs_backuper has started")

    client_id = set_id_and_secret(
        secret_file_name_=secret_file_name
    )["client_id"]
    client_secret = set_id_and_secret(
        secret_file_name_=secret_file_name
    )["client_secret"]

    creds = get_user_credentials_with_try(
        scopes, client_id, client_secret
    )

    loop_nb = 0
    with daemon.DaemonContext(
        files_preserve=[
            fh.stream
        ],  # I dont know what .stream property for file handler (pointer) is, but 'files_preserve' needs list of file names i think - https://stackoverflow.com/questions/13180720/maintaining-logging-and-or-stdout-stderr-in-python-daemon
        working_directory=getcwd(),
        stderr=stderr,
    ):
        while True:
            try:
                # Construct a Resources/services for interacting with an API. Building a Python representation of the API
                mail = build_service_image(
                    serviceName_="gmail",
                    version_="v1",
                    credentials_=creds,
                )
                drive = build_service_image(
                    serviceName_="drive",
                    version_="v3",
                    credentials_=creds,
                    mail_=mail,
                )

                files = get_list_of_files(drive, mail)

                # list of files of interest. This is a way to make dataframes in padnas work...
                new_files_of_interest = pandas.DataFrame(
                    data={
                        "ID": [],
                        "ModifiedTime": [],
                        "Name": [],
                        "MimeType": [],
                    },
                    dtype=str,
                )

                # Here we write a dataframe of google documents currently in the drive
                for file in files:
                    if file["mimeType"] in [
                        "application/vnd.google-apps.document",
                        "application/vnd.google-apps.spreadsheet",
                        "application/vnd.google-apps.presentation",
                    ]:  # So for now lets return only google docs. I dunno if we want to backup everything there is on the drive
                        new_files_of_interest = new_files_of_interest.append(
                            other=pandas.DataFrame(
                                data={
                                    "ID": [file["id"]],
                                    "ModifiedTime": [
                                        file["modifiedTime"]
                                    ],
                                    "Name": [file["name"]],
                                    "MimeType": [
                                        file["mimeType"]
                                    ],
                                },
                                dtype=str,
                            )
                        )  #

                # Here we either download all google documents, if this is a first time the script is running, or we identify which documents chages since last time, and we download only those. It would be nice to limit number of documents to 100 or 1000 and sign them with data of download
                if (
                    path.isfile("files_of_interest.csv")
                    == True
                ):
                    old_files_of_interest = pandas.read_csv(
                        "files_of_interest.csv"
                    )

                    combined_files_of_interest = new_files_of_interest.merge(
                        right=old_files_of_interest,
                        how="left",
                        on="ID",
                        suffixes=("_new", "_old"),
                    )

                    write_new_files_of_interest_file(
                        new_files_of_interest_=new_files_of_interest,
                        mail_=mail,
                    )

                    ### Run this to finalize the file download
                    combined_files_of_interest.apply(
                        func=lambda a: download_the_file_with_changed_modification_time(
                            Id=a.ID,
                            Mod_time_old=a.ModifiedTime_old,
                            Mod_time_new=a.ModifiedTime_new,
                            name=a.Name_new,
                            mimetype=a.MimeType_new,
                            drive=drive,
                        ),
                        axis=1,
                    )
                else:
                    # Here we save the first list of google doc files on the drive
                    write_new_files_of_interest_file(
                        new_files_of_interest_=new_files_of_interest,
                        mail_=mail,
                    )

                    # Here we download all files in file list
                    new_files_of_interest.apply(
                        func=lambda a: download_the_file(
                            Id=a.ID,
                            Mod_time=a.ModifiedTime,
                            name=a.Name,
                            mimetype=a.MimeType,
                            drive=drive,
                        ),
                        axis=1,
                    )

                loop_nb = wait_report_back_and_loop(
                    how_frequently_to_check_for_updates,
                    loop_nb,
                    mail,
                )

            except:
                mail = build_service_image(
                    serviceName_="gmail",
                    version_="v1",
                    credentials_=creds,
                )
                excepthook_for_GDocs_loop(mail)


if __name__ == "__main__":
    main()
