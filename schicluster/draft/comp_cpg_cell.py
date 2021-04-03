# command time python /gale/ddn/snm3C/humanPFC/code/comp_cpg_cell.py --indir /gale/raidix/rdx-5/zhoujt/projects/methylHiC/PFC_batch_merged/smoothed_matrix/1cell/${res0}b_resolution/ --outdir /gale/ddn/snm3C/humanPFC/smoothed_matrix/${res0}b_resolution/ --cell $(cat /gale/ddn/snm3C/humanPFC/smoothed_matrix/celllist_long.txt | head -${SGE_TASK_ID} | tail -1) --chrom ${c} --mode raw --cpg_file /gale/ddn/snm3C/humanPFC/smoothed_matrix/${res0}b_resolution/bins/hg19.${res0}bin.CpG.txt

import h5py
import argparse
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags

def comp_cpg_cell(indir, outdir, cell, chrom, mode, cpg_file):

	if chrom[:3]=='chr':
		c = chrom[3:]
	else:
		c = chrom
	cpg = pd.read_csv(cpg_file, sep='\t', header=0)
	cpg['ratio'] = (cpg['13_user_patt_count'] / (cpg['12_seq_len'] - cpg['10_num_N'])).fillna(0)
	cpg = cpg[(cpg['#1_usercol']==('chr'+c))]['ratio'].values[:,None]
	binfilter = (cpg[:,0]>0)
	if mode=='raw':
		D = np.loadtxt(f'{indir}chr{c}/{cell}_chr{c}.txt')
		if len(D)==0:
			D = np.array([[0,0,0]])
		elif len(D.shape)==1:
			D = D.reshape(1,-1)
		A = csr_matrix((D[:, 2], (D[:, 0], D[:, 1])), shape = (len(cpg), len(cpg)))
	else:
		with h5py.File(f'{indir}chr{c}/{cell}_chr{c}_{mode}.hdf5', 'r') as f:
			g = f['Matrix']
			A = csr_matrix((g['data'][()], g['indices'][()], g['indptr'][()]), g.attrs['shape'])
	A = A - diags(A.diagonal())
	A = A + A.T
	A = A + diags((A.sum(axis=0).A.ravel()==0).astype(int))
	# normalize row sum to 1
	d = diags(1 / A.sum(axis=0).A.ravel())
	P = d.dot(A)
	# weighted average of cpg density
	comp = A.dot(cpg)[:,0]
	tmp = comp[binfilter]
	Apos = (tmp > np.percentile(tmp, 80))
	Bpos = (tmp < np.percentile(tmp, 20))
	E = A.tocoo()
	decay = np.array([E.diagonal(i).mean() for i in range(E.shape[0])])
	E.data = E.data / decay[np.abs(E.col - E.row)]
	E = E.tocsr()[np.ix_(binfilter, binfilter)]
	score = [E[np.ix_(Apos, Apos)].sum(), E[np.ix_(Bpos, Bpos)].sum(), E[np.ix_(Apos, Bpos)].sum()]
	np.save(f'{outdir}chr{c}/{cell}_chr{c}_{mode}.cpgcomp.npy', comp.tolist() + score)
	return

parser = argparse.ArgumentParser()
parser.add_argument('--indir', type=str, default=None, help='Directory of raw/imputed matrices end with /')
parser.add_argument('--outdir', type=str, default=None, help='Directory of compartment matrix end with /')
parser.add_argument('--cell', type=str, default=None, help='Full path of a file containing a list of cell identifiers to be concatenate')
parser.add_argument('--chrom', type=str, default=None, help='Chromosome to impute')
parser.add_argument('--mode', type=str, default=None, help='Suffix of imputed matrix file names')
parser.add_argument('--cpg_file', type=str, default=None, help='CpG counts generated by bedtools nuc')
opt = parser.parse_args()

comp_cpg_cell(opt.indir, opt.outdir, opt.cell, opt.chrom, opt.mode, opt.cpg_file)