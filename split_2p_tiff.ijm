t0=getTime()

print("Running macro to split 2photon tiff into chunks");

argString = getArgument();
args = split(argString, "(, )");

filename = args[0];
proj = args[1];
framesPerChunk = args[2];
z = args[3];

print("File to be processed is", filename);
print("Using", proj, "projection");
print("Number of frames per chunk is", framesPerChunk);
print("Number of z planes is", z);

//open tiff (give label if possible)
run("Bio-Formats Importer", "open=" + filename + " color_mode=Default view=Hyperstack stack_order=XYCZT");
print((getTime() - t0) / 1000, " : File opened.");

fileStub = File.nameWithoutExtension;
saveDir = File.directory + File.separator + "chunks";
File.makeDirectory(saveDir);

print("Total number of slices is", nSlices());

while(nSlices() % 3 > 0) {
	setSlice(nSlices());
	run("Delete Slice");
}

//make z project
zprojectString = "order=xyczt(default) channels=1 slices=" + z + " frames="+ nSlices()/z + " display=Grayscale";
run("Stack to Hyperstack...", zprojectString);
run("Z Project...", "projection=[Max Intensity] all");
print((getTime() - t0) / 1000, " : Z-projection complete.");

print("Number of frames after processing is", nSlices());

i=1;

while (nSlices() > framesPerChunk) {
	print(nSlices());
	range="1-" + framesPerChunk;
	run("Make Substack...", "slices=" + range + " delete");
	saveAs("Tiff", saveDir + File.separator + "0" + i + "_" + fileStub);
	close();
	i++;
}

saveAs("Tiff", saveDir + File.separator + "0" + i + "_" + fileStub);
print((getTime() - t0) / 1000, " : All files saved.");
print("Saved file as", i, "chunks. Exiting.");

