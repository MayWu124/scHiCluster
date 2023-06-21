"""
CLI defined here

When adding new function:
1. add a func_register_subparser function to register the subparser
2. add a condition in main func about this new func name, import the real func as func in main
"""
import schicluster
from schicluster import __version__

import argparse
import inspect
import subprocess
import sys
import logging
import os

os.environ["NUMEXPR_MAX_THREADS"] = "8"

log = logging.getLogger()

DESCRIPTION = """
scHiCluster is a toolkit for single-cell HiC data preprocessing, imputation, and clustering analysis.

Current Tool List in scHiCluster:

"""

EPILOG = ''


class NiceFormatter(logging.Formatter):
    """
    From Cutadapt https://github.com/marcelm/cutadapt
    Do not prefix "INFO:" to info-level log messages (but do it for all other
    levels).
    Based on http://stackoverflow.com/a/9218261/715090 .
    """

    def format(self, record):
        if record.levelno != logging.INFO:
            record.msg = '{}: {}'.format(record.levelname, record.msg)
        return super().format(record)


def validate_environment():
    try:
        # TODO add env validation here
        subprocess.run(['bedtools', '--version'],
                       stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       encoding='utf8',
                       check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise e
    return True


def setup_logging(stdout=False, quiet=False, debug=False):
    """
    From Cutadapt https://github.com/marcelm/cutadapt
    Attach handler to the global logger object
    """
    # Due to backwards compatibility, logging output is sent to standard output
    # instead of standard error if the -o option is used.
    stream_handler = logging.StreamHandler(sys.stdout if stdout else sys.stderr)
    stream_handler.setFormatter(NiceFormatter())
    # debug overrides quiet
    if debug:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    stream_handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(stream_handler)


def _str_to_bool(v: str) -> bool:
    if v.lower() in {'true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh'}:
        return True
    else:
        return False


def comp_cpg_cell_register_subparser(subparser):
    parser = subparser.add_parser('comp-cpg-cell',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--indir', type=str, default=None,
                            help='Directory of raw/imputed matrices end with /')

    parser_req.add_argument('--outdir', type=str, default=None,
                            help='Directory of compartment matrix end with /')

    parser_req.add_argument('--cell', type=str, default=None,
                            help='Specific identifier of a cell')

    parser_req.add_argument('--chrom', type=str, default=None,
                            help='Chromosome to compute compartment')

    parser.add_argument('--mode', type=str, default=None,
                        help='Suffix of imputed matrix file names or raw')

    parser.add_argument('--cpg_file', type=str, default=None,
                        help='CpG counts generated by bedtools nuc')


def comp_concatcell_chr_register_subparser(subparser):
    parser = subparser.add_parser('comp-concatcell-chr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_list', type=str, default=None,
                            help='Full path of a file containing the full path of all CpG npy files to be concatenate')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of concatenated matrix including directory')

    parser.add_argument('--ncpus', type=int, default=10,
                        help='# threads for parallelization')


def domain_insulation_cell_register_subparser(subparser):
    parser = subparser.add_parser('domain-insulation-cell',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--indir', type=str, default=None,
                            help='Directory of imputed matrices end with /')

    parser_req.add_argument('--cell', type=str, default=None,
                            help='Specific identifier of a cell')

    parser_req.add_argument('--chrom', type=str, default=None,
                            help='Chromosome to compute insulation score')

    parser_req.add_argument('--mode', type=str, default=None,
                            help='Suffix of imputed matrix file names')

    parser.add_argument('--w', type=int, default=10,
                        help='Window size for insulation score')


def domain_concatcell_chr_register_subparser(subparser):
    parser = subparser.add_parser('domain-concatcell-chr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_list', type=str, default=None,
                            help='Full path of a file containing the full path of all insulation npy or domain txt files to be concatenate')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of concatenated matrix including directory')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer')

    parser.add_argument('--input_type', type=str, default='insulation',
                        help='Whether input files are insulation.npy or domain.txt')  # insulation or boundary

    parser.add_argument('--ncpus', type=int, default=10,
                        help='# threads for parallelization')


def embed_concatcell_chr_register_subparser(subparser):
    parser = subparser.add_parser('embed-concatcell-chr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_list', type=str, default=None,
                            help='Full path of a file containing the full path to all imputed matrices to be concatenate')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of concatenated matrix including directory')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer of imputed matrices')

    parser.add_argument('--dist', type=int, default=10000000,
                        help='Maximum distance threshold of contacts to use')

    parser.add_argument('--skip_raw', dest='save_raw', action='store_false',
                        help='Not to save cell-by-feature matrix before SVD')
    parser.set_defaults(save_raw=True)

    parser.add_argument('--dim', type=int, default=50,
                        help='Number of dimensions to return from SVD')


def embed_mergechr_register_subparser(subparser):
    parser = subparser.add_parser('embed-mergechr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--embed_list', type=str, default=None,
                            help='Full path of a file containing the full path to dimension reduction files of all chromosomes')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of final dimension reduction file including directory')

    parser.add_argument('--dim', type=int, default=20,
                        help='Number of dimensions to return from SVD')

    parser.add_argument('--use_pc', dest='norm_sig', action='store_false',
                        help='Not to normalize PCs by singular values')
    parser.set_defaults(norm_sig=True)


def generatematrix_cell_register_subparser(subparser):
    parser = subparser.add_parser('generatematrix-cell',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help='')

    parser_req = parser.add_argument_group('required arguments')
    parser_req.add_argument('--infile', type=str, default=None,
                            help='Path to the short format contact file')

    parser_req.add_argument('--outdir', type=str, default=None,
                            help='Output directory end with /')

    parser_req.add_argument('--cell', type=str, default=None,
                            help='Specific identifier of a cell')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer to generate contact matrix')

    parser_req.add_argument('--chrom_file', type=str, default=None,
                            help='Path to the chromosome size files containing all chromosome to be analyzed as the first column')

    parser.add_argument('--split_file', type=str, default=None,
                        help='Path to the bed file containing all chromosomes need to split and one region per chromosome as splitting point')

    parser.add_argument('--chr1', type=int, default=1,
                        help='Column of fragment1 chromosome, counting starts from 0')

    parser.add_argument('--pos1', type=int, default=2,
                        help='Column of fragment1 position, counting starts from 0')

    parser.add_argument('--chr2', type=int, default=5,
                        help='Column of fragment2 chromosome, counting starts from 0')

    parser.add_argument('--pos2', type=int, default=6,
                        help='Column of fragment2 position, counting starts from 0')

    parser.add_argument('--dist', type=int, default=2500,
                        help='Minimum distance threshold of contacts to use')


def impute_cell_register_subparser(subparser):
    parser = subparser.add_parser('impute-cell',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--indir', type=str, default=None,
                            help='Directory of the contact matrix')

    parser_req.add_argument('--outdir', type=str, default=None,
                            help='Output directory end with /')

    parser_req.add_argument('--cell', type=str, default=None,
                            help='Specific identifier of a cell')

    parser_req.add_argument('--chrom', type=str, default=None,
                            help='Chromosome to impute')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer to generate contact matrix')

    parser_req.add_argument('--chrom_file', type=str, default=None,
                            help='Path to the chromosome size files containing all chromosomes to be analyzed')

    parser.add_argument('--logscale', dest='logscale', action='store_true',
                        help='Log transform raw count')
    parser.set_defaults(logscale=False)

    parser.add_argument('--pad', type=int, default=1,
                        help='Gaussian kernal size')

    parser.add_argument('--std', type=float, default=1,
                        help='Gaussian kernal standard deviation')

    parser.add_argument('--rp', type=float, default=0.5,
                        help='Restart probability of RWR')

    parser.add_argument('--tol', type=float, default=0.01,
                        help='Convergence tolerance of RWR')

    parser.add_argument('--window_size', type=int, default=500000000,
                        help='Size of RWR sliding window')

    parser.add_argument('--step_size', type=int, default=10000000,
                        help='Step length of RWR sliding window')

    parser.add_argument('--output_dist', type=int, default=500000000,
                        help='Maximum distance threshold of contacts when writing output file')

    parser.add_argument('--output_format', type=str, default='hdf5',
                        help='Output file format (hdf5 or npz)')

    parser.add_argument('--mode', type=str, default=None,
                        help='Suffix of output file name')


def loop_bkg_cell_register_subparser(subparser):
    parser = subparser.add_parser('loop-bkg-cell',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--indir', type=str, default=None,
                            help='Directory of imputed matrix')

    parser_req.add_argument('--cell', type=str, default=None,
                            help='Specific identifier of a cell')

    parser_req.add_argument('--chrom', type=str, default=None,
                            help='Chromosome to compute background')

    parser_req.add_argument('--impute_mode', type=str, default=None,
                            help='Suffix of imputed matrix file names')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer to generate contact matrix')

    parser.add_argument('--dist', type=int, default=10050000,
                        help='Maximum distance threshold of contacts to use')

    parser.add_argument('--cap', type=int, default=5,
                        help='Trim Z-scores over the threshold')

    parser.add_argument('--pad', type=int, default=5,
                        help='One direction size of larger square for donut background')

    parser.add_argument('--gap', type=int, default=2,
                        help='One direction size of smaller square for donut background')

    parser.add_argument('--norm_mode', type=str, default='dist_trim',
                        help='Suffix of normalized file names')


def loop_sumcell_chr_register_subparser(subparser):
    parser = subparser.add_parser('loop-sumcell-chr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_list', type=str, default=None,
                            help='Full path of a file containing the full path of all imputed files to be summed without .hdf5 suffix')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of summed matrix including directory')

    parser_req.add_argument('--res', type=int, default=None,
                            help='Bin size as integer of imputed matrices')

    parser.add_argument('--group_list', type=str, default=None,
                        help='Full path of a file containing the full path of all summed imputed files to be merged without .hdf5 suffix')

    parser.add_argument('--matrix', type=str, default='QEO',
                        help='Types of matrices to merge (Q: imputed matrix; E: OVE matrix; O: Outlier matrix)')

    parser.add_argument('--sum_only', dest='sum_only', action='store_true',
                        help='Sum cells only and do not test for loops')
    parser.set_defaults(sum_only=False)

    parser.add_argument('--test_only', dest='test_only', action='store_true',
                        help='Sum of cells already exist and do loop test only')
    parser.set_defaults(test_only=False)

    parser.add_argument('--norm_mode', type=str, default='dist_trim',
                        help='Suffix of normalized file names')

    parser.add_argument('--min_dist', type=int, default=50000,
                        help='Minimum distance threshold of loop')

    parser.add_argument('--max_dist', type=int, default=10000000,
                        help='Maximum distance threshold of loop')

    parser.add_argument('--pad', type=int, default=5,
                        help='One direction size of larger square for donut background')

    parser.add_argument('--gap', type=int, default=2,
                        help='One direction size of smaller square for donut background')


def loop_mergechr_register_subparser(subparser):
    parser = subparser.add_parser('loop-mergechr',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--inprefix', type=str, default=None,
                            help='Prefix of summed matrix including directory')

    parser_req.add_argument('--outprefix', type=str, default=None,
                            help='Prefix of loop files including directory')

    parser_req.add_argument('--chrom_file', type=str, default=None,
                            help='Path to the chromosome size files containing all chromosome to be analyzed as the first column')

    parser.add_argument('--split_file', type=str, default=None,
                        help='Path to the bed file containing all chromosomes need to split and one region per chromosome as splitting point')

    parser.add_argument('--res', type=int, default=10000,
                        help='Bin size as integer of loop calling')

    parser.add_argument('--thres_bl', type=int, default=1.33,
                        help='Lowest fold change threshold against bottom left background')

    parser.add_argument('--thres_d', type=int, default=1.33,
                        help='Lowest fold change threshold against donut background')

    parser.add_argument('--thres_h', type=int, default=1.2,
                        help='Lowest fold change threshold against horizontal background')

    parser.add_argument('--thres_v', type=int, default=1.2,
                        help='Lowest fold change threshold against vertical background')

    parser.add_argument('--fdr_thres', type=int, default=0.1,
                        help='Highest t-test FDR threshold of loops')

    parser.add_argument('--dist_thres', type=int, default=20000,
                        help='Highest distance threshold to merge loops into summit')

    parser.add_argument('--size_thres', type=int, default=1,
                        help='Lowest loop number threshold of summit')


def generate_scool_register_subparser(subparser):
    parser = subparser.add_parser('generate-scool',
                                  aliases=['scool'],
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--contacts_table', type=str, required=True, default=None,
                            help='tab-separated table containing tow columns, 1) cell id, '
                                 '2) cell contact file path (juicer-pre format). No header')
    parser_req.add_argument('--output_prefix', type=str, required=True, default=None,
                            help='Output prefix of the scool files. '
                                 'Output path will be {output_prefix}.{resolution_str}.scool')
    parser_req.add_argument('--chrom_size_path', type=str, required=True, default=None,
                            help='Path to the chromosome size file, this file should be in UCSC chrom.sizes format. '
                                 'We will use this file as the reference to create matrix. '
                                 'It is recommended to remove small contigs or chrM from this file.')
    parser_req.add_argument('--resolutions', type=int, nargs='+', required=True, default=[],
                            help='Resolutions to generate the matrix. '
                                 'You can provide multiple resolutions separated by space, '
                                 '(e.g., "--resolutions 10000 100000"). '
                                 'Each resolution will be stored in a separate file.')
    parser.add_argument('--blacklist_1d_path', type=str, required=False, default=None,
                        help='Path to blacklist region BED file, such as ENCODE blacklist. '
                             'Either side of the contact overlapping with a blacklist region will be removed.')
    parser.add_argument('--blacklist_2d_path', type=str, required=False, default=None,
                        help='Path to blacklist region pair BEDPE file. '
                             'Both side of the contact overlapping with the same '
                             'blacklist region pair will be removed.')
    parser.add_argument('--blacklist_resolution', type=int, default=10000, required=False,
                        help='Resolution in bps when consider the 2D blacklist region pairs.')
    parser.add_argument('--not_remove_duplicates', dest='remove_duplicates', action='store_false',
                        help='If set, will NOT remove duplicated contacts based on '
                             '[chr1, pos1, chr2, pos2] values')
    parser.set_defaults(remove_duplicates=True)
    parser.add_argument('--chr1', type=int, default=1, help='0 based index of chr1 column.')
    parser.add_argument('--chr2', type=int, default=5, help='0 based index of chr2 column.')
    parser.add_argument('--pos1', type=int, default=2, help='0 based index of pos1 column.')
    parser.add_argument('--pos2', type=int, default=6, help='0 based index of pos2 column.')
    parser.add_argument('--min_pos_dist', type=int, default=2500,
                        help='Minimum distance for a fragment to be considered.')
    parser.add_argument('--cpu', type=int, default=1, help='number of cpus to parallel.')
    parser.add_argument('--batch_n', type=int, default=50, help='number of cells to deal with in each cpu process.')


def prepare_imputation_register_subparser(subparser):
    parser = subparser.add_parser('imputation',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--input_scool', type=str, required=True, default=None,
                            help='Path to input scool file')
    parser_req.add_argument('--output_dir', type=str, required=True, default=None,
                            help='Path to output directory')
    parser_req.add_argument('--chrom_size_path', type=str, required=True, default=None,
                            help='Path to chromosome sizes file')
    parser_req.add_argument('--output_dist', type=int, required=True, default=None,
                            help='')
    parser_req.add_argument('--window_size', type=int, required=True, default=None,
                            help='')
    parser_req.add_argument('--step_size', type=int, required=True, default=None,
                            help='')
    parser_req.add_argument('--resolution', type=int, required=True, default=None,
                            help='')

    parser.add_argument('--batch_size', type=int, required=False, default=100,
                        help='')
    parser.add_argument('--logscale', dest='logscale', action='store_true',
                        help='')
    parser.set_defaults(logscale=False)
    parser.add_argument('--pad', type=int, required=False, default=1,
                        help='')
    parser.add_argument('--std', type=int, required=False, default=1,
                        help='')
    parser.add_argument('--rp', type=float, required=False, default=0.5,
                        help='')
    parser.add_argument('--tol', type=float, required=False, default=0.01,
                        help='')
    parser.add_argument('--min_cutoff', type=float, required=False, default=1e-5,
                        help='')
    parser.add_argument('--cpu_per_job', type=int, required=False, default=10,
                        help='')
    return


def call_domain_register_subparser(subparser):
    parser = subparser.add_parser('domain',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_table_path', type=str, required=True, default=None,
                            help='Path to cell table file')
    parser_req.add_argument('--output_prefix', type=str, required=True, default=None,
                            help='Output files prefix. '
                                 'The domain boundary matrix will be saved as '
                                 '{output_prefix}.boundary.h5ad (anndata.AnnData); '
                                 'The insulation score matrix will be saved as '
                                 '{output_prefix}.insulation.nc (xarray.DataSet)')
    parser.add_argument('--resolution', type=int, required=False, default=25000,
                        help='Matrix resolution')
    parser.add_argument('--window_size', type=int, required=False, default=10,
                        help='Window size for calculating insulation score')
    parser.add_argument('--cpu', type=int, required=False, default=10,
                        help='Number of CPUs to use')


def call_compartment_register_subparser(subparser):
    parser = subparser.add_parser('compartment',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_table_path', type=str, required=True, default=None,
                            help='Path to cell table file')
    parser_req.add_argument('--output_prefix', type=str, required=True, default=None,
                            help='Output files prefix. '
                                 'The compartment score matrix will be saved as '
                                 '{output_prefix}.compartment.h5ad (anndata.AnnData).')
    parser_req.add_argument('--cpg_profile_path', type=str, required=True, default=None,
                            help='Genome bins CpG ratio. Use "schicluster cpg-ratio" to calculate')
    parser.add_argument('--cpu', type=int, required=False, default=10,
                        help='Number of CPUs to use')
    parser.add_argument('--calc_strength', dest='calc_strength', action='store_true',
                        help='Calculate compartment strength summary')
    parser.set_defaults(calc_strength=False)
    return


def cpg_ratio_register_subparser(subparser):
    parser = subparser.add_parser('cpg-ratio',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_url', type=str, required=True, default=None,
                            help='Path to a cell Cooler URL')
    parser_req.add_argument('--fasta_path', type=str, required=True, default=None,
                            help='Path to genome FASTA file')
    parser_req.add_argument('--hdf_output_path', type=str, required=True, default=None,
                            help='Output path of the CpG ratio')


def embedding_register_subparser(subparser):
    parser = subparser.add_parser('embedding',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_table_path', type=str, required=True, default=None,
                            help='Path to cell table file')
    parser_req.add_argument('--output_dir', type=str, required=True, default=None,
                            help='Path to embedding output dir')
    parser.add_argument('--dim', type=int, required=False, default=50,
                        help='')
    parser.add_argument('--dist', type=int, required=False, default=1000000,
                        help='')
    parser.add_argument('--resolution', type=int, required=False, default=100000,
                        help='')
    parser.add_argument('--scale_factor', type=int, required=False, default=100000,
                        help='')
    parser.add_argument('--cpu', type=int, required=False, default=1,
                        help='')
    parser.add_argument('--norm_sig', dest='norm_sig', action='store_true',
                        help='')
    parser.set_defaults(norm_sig=False)
    parser.add_argument('--save_model', dest='save_model', action='store_true',
                        help='')
    parser.set_defaults(save_model=False)
    parser.add_argument('--save_raw', dest='save_raw', action='store_true',
                        help='')
    parser.set_defaults(save_raw=False)

def gene_score_register_subparser(subparser):
    parser = subparser.add_parser('gene-score',
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  help="")

    parser_req = parser.add_argument_group("required arguments")
    parser_req.add_argument('--cell_table', type=str, default=None, 
                            help='Full path to cell cool table')
    parser_req.add_argument('--gene_meta', type=str, default=None, 
                            help='Full path to bed file with region id')
    parser_req.add_argument('--res', type=int, default=10000, 
                            help='Resolution of cool file')
    parser_req.add_argument('--output_hdf', type=str, default=None, 
                            help='Full path to output file')
    parser_req.add_argument('--chrom_size', type=str, default=None, 
                            help='Chromsome size file with only chromosomes to use')
    parser.add_argument('--cpu', type=int, default=10, 
                        help='CPUs to use')
    parser.add_argument('--slop', type=int, default=0, 
                        help='gene slop distance on both sides')
    parser.add_argument('--mode', type=str, default='impute', 
                        help='raw or impute')

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION,
                                     epilog=EPILOG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     )
    subparsers = parser.add_subparsers(
        title="functions",
        dest="command",
        metavar=""
    )

    # add subparsers
    current_module = sys.modules[__name__]
    # get all functions in parser
    for name, register_subparser_func in inspect.getmembers(current_module, inspect.isfunction):
        if 'register_subparser' in name:
            register_subparser_func(subparsers)

    # initiate
    args = None
    if len(sys.argv) > 1:
        # print out version
        if sys.argv[1] in ['-v', '--version']:
            print(schicluster.__version__)
            exit()
        else:
            args = parser.parse_args()
    else:
        # print out help
        parser.parse_args(["-h"])
        exit()

    # set up logging
    if not logging.root.handlers:
        setup_logging(stdout=True,
                      quiet=False)
    # execute command
    args_vars = vars(args)
    for k, v in args_vars.items():
        log.info(f'{k}\t{v}')

    cur_command = args_vars.pop('command').lower().replace('_', '-')
    # Do real import here:
    if cur_command in ['generatematrix-cell']:
        from .draft.generatematrix_cell import generatematrix_cell as func
    elif cur_command in ['impute-cell']:
        from .draft.impute_cell import impute_cell as func
    elif cur_command in ['embed-concatcell-chr']:
        from .draft.embed_concatcell_chr import embed_concatcell_chr as func
    elif cur_command in ['embed-mergechr']:
        from .draft.embed_mergechr import embed_mergechr as func
    elif cur_command in ['loop-bkg-cell']:
        from .draft.loop_bkg_cell import loop_bkg_cell as func
    elif cur_command in ['loop-sumcell-chr']:
        from .draft.loop_sumcell_chr import loop_sumcell_chr as func
    elif cur_command in ['loop-mergechr']:
        from .draft.loop_mergechr import loop_mergechr as func
    elif cur_command in ['domain-insulation-cell']:
        from .draft.domain_insulation_cell import domain_insulation_cell as func
    elif cur_command in ['domain-concatcell-chr']:
        from .draft.domain_concatcell_chr import domain_concatcell_chr as func
    elif cur_command in ['comp-cpg-cell']:
        from .draft.comp_cpg_cell import comp_cpg_cell as func
    elif cur_command in ['comp-concatcell-chr']:
        from .draft.comp_concatcell_chr import comp_concatcell_chr as func
    elif cur_command in ['generate-scool', 'scool']:
        from .cool import generate_scool as func
    elif cur_command in ['imputation']:
        from .impute import prepare_impute as func
    elif cur_command in ['domain']:
        from .domain import multiple_call_domain_and_insulation as func
    elif cur_command in ['compartment']:
        from .compartment import multiple_cell_compartment as func
    elif cur_command in ['cpg-ratio']:
        from .compartment import get_cpg_profile as func
    elif cur_command in ['embedding']:
        from .embedding import embedding as func
    elif cur_command in ['gene-score']:
        from .draft.gene_score import gene_score as func
    else:
        log.debug(f'{cur_command} is not an valid sub-command')
        parser.parse_args(["-h"])
        return

    # run the command
    log.info(f"hicluster: Executing {cur_command}...")
    func(**args_vars)
    log.info(f"{cur_command} finished.")
    return


if __name__ == '__main__':
    main()
