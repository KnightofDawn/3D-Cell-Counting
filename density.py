from scipy.ndimage.filters import gaussian_filter
import h5py
from os.path import join, normpath
from os import mkdir, sep
from shutil import rmtree
from matplotlib.gridspec import GridSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable

'''
Produces heatmaps from image data found in data.h5
'''

PATH = "/path/to/data.h5"
datafile = join(PATH, "data.h5")
outdir = "/tmp/images"
try:
  rmtree(outdir)
except OSError:
  pass

mkdir(outdir)

psmooth = 0.100 #diamter over which average cell density is computed; can be thought of as estimate of diameter of "interesting features"

unit_conversion = 1000 # meters to mm

def vis(name, obj):
  
  data = obj[:]
  
  name = "result_" + name
  
  raw_image = data.sum(-1)
  raw_image.T[:] -= raw_image.min(tuple(range(1, raw_image.ndim)))
  raw_image.T[:] /= raw_image.max(tuple(range(1, raw_image.ndim)))
  
  pad_width = ((0,1),) + ((0,0),) * (raw_image.ndim - 1)
  raw_image = pad(raw_image, pad_width=pad_width, mode='constant', constant_values=0)
  raw_image = raw_image.transpose(roll(range(raw_image.ndim), -1))
  
  scale = obj.attrs['scale'][:] * unit_conversion
  X = (scale * data.shape[1:])[1::-1]
  
  extent = [0, X[0], 0, X[1]]

  for measure, data1 in zip(("Nucleus", "Actin"), data):
    
    psmooth0 = psmooth / scale
    
    smoothed_data = gaussian_filter(data1, psmooth0).sum(2)
    smoothed_data -= smoothed_data.min()
    smoothed_data /= smoothed_data.max()
    
    dp = (scale * psmooth0)[:2].mean()
    
    clf()
    fig = figure(figsize(22, 10))
    
    gs = GridSpec(1, 2)
    ax = []
    for gs0 in gs:
      ax0 = fig.add_subplot(gs0)
      ax0.set_adjustable("box-forced")
      ax0.set_xlabel("mm", fontsize="x-large")
      ax0.set_ylabel("mm", fontsize="x-large")
      ax.append(ax0)
      
    
    divider = make_axes_locatable(ax[0])
    cax = divider.append_axes("right", size="5%", pad=0.05)
    im = ax[0].imshow(smoothed_data, extent=extent, interpolation="bicubic", origin="lower")
    cb = colorbar(im, cax=cax)
    cb.set_label(label="{} Density".format(measure), fontsize="x-large")
      
    ax[1].imshow(raw_image, extent=extent, interpolation="bilinear", origin="lower")
    
    gs.tight_layout(fig)
    savefig(join(outdir, name + "_{}.png".format(measure)))
    
def enum_h5(f):
  keys = []
  for key in f.keys():
    try:
      subkeys = enum_h5(f[key])
    except AttributeError:
      keys.append([key])
      continue
      
    for subkey in subkeys:
      keys.append([key] + subkey)
      
  return keys

with h5py.File(datafile) as f:
  for key in enum_h5(f)[:]:
    vis("_".join(key), f["/".join(key)])
