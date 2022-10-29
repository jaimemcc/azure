#!/bin/bash

while getopts u:f:p:c:z flag
do
    case "${flag}" in
        u) update=${OPTARG};;
        f) filename=${OPTARG};;
        p) projection=${OPTARG};;
        c) chunks=${OPTARG};;
        z) zplanes=${OPTARG};;
    esac
done

if $update; then
    echo "Updating imageJ macro...";
    cp ./split_2p_tiff.ijm ~/Fiji.app/macros/split_2p_tiff.ijm;
fi

if ["$filename" = ""]; then
    filename="/mnt/d/Test Data/2photon/221003/03_max_subset/MAX_file_00003_subset_299_frames.tif"
fi

if ["$projection" = ""]; then
    projection="max"
fi

if ["$chunks" = ""]; then
    chunks="6000"
fi

if ["$zplanes" = ""]; then
    zplanes="3"
fi

# xvfb-run-safe ~/Fiji.app/ImageJ-linux64 --headless -macro split_2p_tiff.ijm "$filename, $projection, $chunks, $zplanes"
~/Fiji.app/ImageJ-linux64 -macro split_2p_tiff.ijm "$filename, $projection, $chunks, $zplanes"

# https://forum.image.sc/t/how-do-i-prevent-bioformats-from-breaking-fijis-headless-mode/51277/2
# https://imagej.net/learn/headless#Xvfb
# https://list.nih.gov/cgi-bin/wa.exe?A2=IMAGEJ;5ace1ed0.1508