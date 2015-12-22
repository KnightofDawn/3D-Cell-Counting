from glob import glob
from os import walk, sep, remove
from os.path import join, basename
from bs4 import BeautifulStoneSoup
import h5py

main_folder = "/path/to/data files"
'''
data should be stored in hirarchy of folders with descriptive names of experiments

For example:
Set of Experiments 1/
          Experiment 1/
                        ch 0
                        .
                        .
                        .
                        MetaData
          
          Experiment 2/
                        ch 0
                        .
                        .
                        .
                        MetaData
                        
Set of Experiments 2/
          Experiment 1/
                        ch 0
                        .
                        .
                        .
                        MetaData
          
          Experiment 2/
                        ch 0
                        .
                        .
                        .
                        MetaData
Each experiment should contain the following folders:
"ch 0", "ch 1", "ch 2", etc containing a series of tifs representing each layer of the scan
"MetaData" which contains an xml file with the metadata assocaited with the scan
'''

metadata = "MetaData"
labels = ["Voxel-Height", "Voxel-Width", "Voxel-Depth"]

def parse_metadata(filename):
  dims = [None,] * len(labels)
  
  with open (filename, "r") as myfile:
    xml = BeautifulStoneSoup(myfile.read())
  
  maxvals = []
  for channel in xml.Channels:
    maxvals.append(float(channel["Max"]))
    
  for setting in xml.ScannerSetting:
    for i, l in enumerate(labels):
      if setting["Description"] == l:
        dims[i] = float(setting["Variant"])
          
  return maxvals, dims

def organize(root):
  
  data_file = join(root, "data.h5")
  
  try:
    remove(data_file)
  except OSError:
    pass
  
  data_handler = h5py.File(data_file, "w")
    
  for path, dirs, files in walk(root):
    if not metadata in dirs:
    	continue
    
	
    xmls = glob(join(path, metadata, "*.xml"))
    xmls.sort()
    xml_file = xmls[0]
    
    maxvals, dims = parse_metadata(xml_file)
    
    dirs.remove(metadata)
    dirs.sort()
    
    data = []
    for mv, folder in zip(maxvals, dirs):
      images = glob(join(path, folder, "*.tif"))
      images.sort()
      data0 = []
      for image in images:
        data0.append(imread(image))
      
      data0 = asarray(data0, dtype="float") / mv
      data.append(data0.transpose(tuple(range(1, data0.ndim)) + (0,)))
      
    
    data = asarray(data)
    
    path = "/".join(path[len(root):].split(sep))
    path = "/" + path
    data_handler[path] = data
    data_handler[path].attrs['scale'] = dims
    
  data_handler.close()
  
  return data_file
    
organize(main_folder)
