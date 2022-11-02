
import sys
import getopt
import os
import subprocess
import json
import logging

from datetime import datetime

import pandas as pd

from suite2p import default_ops, run_s2p

sys.path.append("~/Github/azure")

# get and parse options
def parse_args(argv, config_data):
    args_dict = {}
    args_dict["metafile"] = False
    args_dict["animals"] = ""
    args_dict["dates"] = ""
    args_dict["imagej"] = False
    args_dict["suite2p"] = False
    args_dict["overwrite"] = False
    args_dict["project_dir"] = config_data["path_to_project_dir"]
    args_dict["get_data"] = False
    args_dict["get_behav_data"] = False
    arg_help = "{} -a <animals> -d <dates>".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hmisogbp:a:d:")
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)
            sys.exit(2)
        elif opt in ("-m", "--get_metafile"):
            args_dict["metafile"] = True
        elif opt in ("-i", "--do_imagej"):
            args_dict["imagej"] = True
        elif opt in ("-s", "--do_suite2p"):
            args_dict["suite2p"] = True
        elif opt in ("-o", "--overwrite"):
            # add line to ask user to confirm overwrite
            args_dict["overwrite"] = True
        elif opt in ("-g", "--get_data"):
            args_dict["get_data"] = True
        elif opt in ("-b", "--get_behav_data"):
            args_dict["get_behav_data"] = True
        elif opt in ("-p", "--project_dir"):
            args_dict["project_dir"] = arg
        elif opt in ("-a", "--animals"):
            args_dict["animals"] = arg
        elif opt in ("-d", "--dates"):
            args_dict["dates"] = arg

    print("Arguments parsed successfully")
    
    return args_dict

f = open("config.json")
config_data = json.load(f)
args_dict = parse_args(sys.argv, config_data)

if not os.path.isdir(args_dict["project_dir"]):
    os.mkdir(args_dict["project_dir"])
    os.mkdir(args_dict["project_dir"], "log")

## setting up logger
logfile = os.path.join(args_dict["project_dir"], "log", "{}.log".format(datetime.now().strftime('%Y-%m-%d_%H:%M:%S')))
logging.basicConfig(filename=logfile,level=logging.DEBUG)

logging.info("Created log file at {}".format(logfile))

if args_dict["metafile"]:
    logging.info("Downloading metafile from remote repo")
    path_to_azcopy = config_data["path_to_azcopy"]
    subprocess.call("{} cp {} {}".format(path_to_azcopy, config_data["metafile"], args_dict["project_dir"]), shell=True)

csv_file = os.path.join(args_dict["project_dir"], os.path.basename(config_data["metafile"]))
print(csv_file)
if not os.path.exists(csv_file):
    print("CSV file cannot be found. Exiting.")
    sys.exit(2)

df = pd.read_csv(csv_file)
print(df.head())

# inspect mouse and date options to produce list of files

if args_dict["animals"] == "all":
    args_dict["animals"] = df["animal"].unique()
elif args_dict["animals"] == "":
    print("No animals given. Exiting")
    sys.exit(2)
else:
    args_dict["animals"] = args_dict["animals"].split()

if args_dict["dates"] == "all":
    args_dict["dates"] = df["date"].unique()
elif args_dict["dates"] == "":
    print("No dates given. Exiting")
    sys.exit(2)
else:
    args_dict["dates"] = args_dict["dates"].split()

print("Analysing", args_dict["animals"], "on", args_dict["dates"])

# make directory structure
path_root = args_dict["project_dir"]
path_raw = os.path.join(path_root, "rawdata")
path_imaging = os.path.join(path_raw, "imaging")
path_behav = os.path.join(path_raw, "behav")
path_processed = os.path.join(path_root, "processeddata")
path_proc_ij = os.path.join(path_processed, "proc_ij")
path_proc_s2p = os.path.join(path_processed, "proc_s2p")

if not os.path.isdir(path_root):
    print("Project path does not exist. Exiting.")
    sys.exit(2)

if not os.path.isdir(path_raw):
    os.mkdir(path_raw)
    os.mkdir(path_imaging)
    os.mkdir(path_behav)
    print("Creating directories for raw data.")

if not os.path.isdir(path_processed):
    os.mkdir(path_processed)
    os.mkdir(path_proc_ij)
    os.mkdir(path_proc_s2p)

    print("Creating directory for processed data.")

def get_session_string_from_df(row):
    date_prefix = "ses-" + row["day"].item().zfill(3)
    date_obj = datetime.strptime(row["date"].item(), "%d/%m/%Y")
    date_suffix = date_obj.strftime("%Y%m%d")
    return date_prefix + "-" + date_suffix

for animal in args_dict["animals"]:

    animal_imaging_path = os.path.join(path_imaging, "sub-{}".format(animal))
    animal_behav_path = os.path.join(path_behav, "sub-{}".format(animal))
    animal_ij_path = os.path.join(path_proc_ij, "sub-{}".format(animal))
    animal_s2p_path = os.path.join(path_proc_s2p, "sub-{}".format(animal))
    
    for path in [animal_imaging_path, animal_behav_path, animal_ij_path, animal_s2p_path]:
        if not os.path.isdir(path):
            os.mkdir(path)

    for date in args_dict["dates"]:
        print("\n***********************************\nNow analysing", animal, date)
        row = df[(df["animal"] == animal) & (df["date"] == date)]
        try:
            ses_path = get_session_string_from_df(row)
        except:
            print("Cannot find matching values for {} on {}. Continuing to next animal/date combination.".format(animal, date))
            continue

        ses_imaging_path = os.path.join(animal_imaging_path, ses_path)
        ses_behav_path = os.path.join(animal_behav_path, ses_path)
        ses_ij_path = os.path.join(animal_ij_path, ses_path)
        ses_s2p_path = os.path.join(animal_s2p_path, ses_path)

        imaging_file_remote = os.path.join(config_data["remote"], row["folder"].item(), row["scanimagefile"].item())
        imaging_file_local = os.path.join(ses_imaging_path, "sub-{}_ses-{}_2p.tif".format(animal, row["day"].item().zfill(3)))

        event_file_remote = os.path.join(config_data["remote"], "behav", row["eventfile"].item())
        event_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_events.csv".format(animal, row["day"].item().zfill(3)))

        frame_file_remote = os.path.join(config_data["remote"], "behav", row["framefile"].item())
        frame_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_frames.csv".format(animal, row["day"].item().zfill(3)))

        lick_file_remote = os.path.join(config_data["remote"], "behav", row["licks"].item())
        lick_file_local = os.path.join(ses_behav_path, "sub-{}_ses-{}_licks.csv".format(animal, row["day"].item().zfill(3)))       

        for path in [ses_imaging_path, ses_behav_path, ses_ij_path, ses_s2p_path]:
            if not os.path.isdir(path):
                 os.mkdir(path)

        if args_dict["get_data"]:
            if len(os.listdir(ses_imaging_path)) > 0:
                if args_dict["overwrite"] == False:
                    print("Files found in {}. If you want to re-download then run the command again with the -o option.".format(ses_imaging_path))
                    continue
                else:
                    i = input("Overwrite option is selected. Do you want to try downloading the raw data again? (y/N)")
                    if i != "y":
                        continue

            print("Downloading imaging data...")
            path_to_azcopy = config_data["path_to_azcopy"]

            subprocess.call("{} cp {}.tif {}".format(path_to_azcopy, imaging_file_remote, imaging_file_local), shell=True)

        if args_dict["get_behav_data"]:
            print("Downloading behavioral data...")

            subprocess.call("{} cp {} {}".format(path_to_azcopy, event_file_remote, event_file_local), shell=True)
            subprocess.call("{} cp {} {}".format(path_to_azcopy, frame_file_remote, frame_file_local), shell=True)
            subprocess.call("{} cp {} {}".format(path_to_azcopy, lick_file_remote, lick_file_local), shell=True)
        # need to add in option to download behav files
        

        # event_file_to_download = row["eventfile"].item()
        # frame_file_to_download = row["framefile"].item()
        # licks_file_to_download = row["licks"].item()
        # print("./download_data {} {} {} {}".format(imaging_file_to_download, event_file_to_download, frame_file_to_download, licks_file_to_download, ses_imaging_path, ses_behav_path))
        # subprocess.call("wsl /mnt/c/github/azure/download_data {} {} {} {}".format(imaging_file_to_download, event_file_to_download, frame_file_to_download, licks_file_to_download, ses_imaging_path, ses_behav_path))
        # # need to write download_data bash script
  
        # do imagej if needed
        if args_dict["imagej"]:
            print("Processing with ImageJ...")
            path_to_imagej = config_data["path_to_imagej"]
            proj = config_data["imagej_settings"]["projection"]
            z = config_data["imagej_settings"]["zplanes"]
            chunks = config_data["imagej_settings"]["framesperchunk"]

            subprocess.call("{} -macro split_2p_tiff.ijm '{}, {}, {}, {}, {}' -batch ".format(path_to_imagej, imaging_file_local, ses_ij_path, proj, chunks, z), shell=True)

        if args_dict["suite2p"]:
            print("Processing with suite2p...")
            db = {'data_path': [ses_ij_path]}
            ops = default_ops()
            ops["save_path0"] = ses_s2p_path
            ops["anatomical_only"] = 3
            ops["diameter"] = 15

            run_s2p(ops=ops,db=db)





# if __name__ == "__main__":
#    parse_args(sys.argv)

### todo
# download_data
# imagej_processing
# suite2p_bash
