# command time python /gale/ddn/snm3C/humanPFC/code/concat_comp.py --cell_list /gale/ddn/snm3C/humanPFC/smoothed_matrix/filelist/cpglist_raw_chr${c}.txt --outprefix /gale/ddn/snm3C/humanPFC/smoothed_matrix/${res0}b_resolution/merged/raw_chr${c} --ncpus 10

import argparse
import numpy as np
from multiprocessing import Pool

def load_cpg(i):
    data = np.load(celllist[i])
    return [i, data[:-3], data[-3:]]

parser = argparse.ArgumentParser()
parser.add_argument('--cell_list', type=str, default=None, help='Full path of a file containing the full path of all CpG npy files to be concatenate')
parser.add_argument('--outprefix', type=str, default=None, help='Prefix of concatenated matrix including directory')
parser.add_argument('--ncpus', type=int, default=10, help='# threads for parallelization')
opt = parser.parse_args()

celllist = np.loadtxt(opt.cell_list, dtype=np.str)
p = Pool(opt.ncpus)
result = p.map(load_cpg, np.arange(len(celllist)))
p.close()
comp = np.zeros((len(celllist), len(result[0][1])))
score = np.zeros((len(celllist), 3))
for i,x,s in result:
	comp[i] = x.copy()
	score[i] = s.copy()

np.save(f'{opt.outprefix}.cpgcomp.npy', comp)
np.save(f'{opt.outprefix}.cpgcompstr.npy', score)
