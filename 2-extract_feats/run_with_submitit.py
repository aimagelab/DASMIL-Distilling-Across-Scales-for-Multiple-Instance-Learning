
import os
import sys
import argparse
import submitit


sys.path.append(os.environ["DINO_REPO"])
sys.path.append(os.environ["MIL4WSI_PATH"])


from  embedding_extraction_tree import processSlide

import utils
import pandas as pd

# Parse command line arguments
parser = argparse.ArgumentParser(
    description='Compute features from Dino embedder')
parser.add_argument('--num_workers', default=4, type=int,
                    help='Number of threads for datalodaer')
parser.add_argument('--norm_layer', default='instance',
                    type=str, help='Normalization layer [instance]')
parser.add_argument("--extractedpatchespath",
                    default="/mnt/beegfs/work/H2020DeciderFicarra/gbontempo/patches/cam_multi", type=str)
parser.add_argument("--savepath", type=str, default="/mnt/beegfs/work/H2020DeciderFicarra/gbontempo/feats/1_XDASMIL/camdinoLevels23All")
parser.add_argument("--levels", type=int, nargs="+",
                    default=[2,3], help="resolution level")
parser.add_argument("--step", type=int, default=1)
parser.add_argument("--job_number", type=int, default=-1)
parser.add_argument('--propertiescsv',
                    default='/homes/gbontempo/DASMIL/2-extract_feats/cam_multi.csv', type=str, help='csv')

parser.add_argument('--model', default='dino', type=str, help='Architecture')
parser.add_argument('--arch', default='vit_small',
                    type=str, help='Architecture')
parser.add_argument('--patch_size', default=16, type=int,
                    help='Patch resolution of the model.')
parser.add_argument('--pretrained_weights1', default='/mnt/beegfs/work/H2020DeciderFicarra/gbontempo/weightsAll/checkpoint.pth',
                    type=str, help="embedder trained at level 1 (scale x20).")
parser.add_argument('--pretrained_weights2', default='/mnt/beegfs/work/H2020DeciderFicarra/gbontempo/weightsAll/checkpoint.pth',
                    type=str, help="embedder trained at level 2 (scale x10)")
parser.add_argument('--pretrained_weights3', default='/mnt/beegfs/work/H2020DeciderFicarra/gbontempo/weightsAll/checkpoint.pth',
                    type=str, help="embedder trained at level 3 (scale x5).")
parser.add_argument('--n_last_blocks', default=4, type=int,
                    help="""Concatenate [CLS] tokens for the `n` last blocks. We use `n=4` when evaluating ViT-Small and `n=1` with ViT-Base.""")
parser.add_argument('--avgpool_patchtokens', default=False, type=utils.bool_flag,
                    help="""Whether ot not to concatenate the global average pooled features to the [CLS] token.
We typically set this to False for ViT-Small and to True with ViT-Base.""")
parser.add_argument("--checkpoint_key", default="teacher", type=str,
                    help='Key to use in the checkpoint (example: "teacher")')
args, _ = parser.parse_known_args()
args.levels = list(args.levels)

# Create an AutoExecutor instance
executor = submitit.AutoExecutor(folder="./loggraph", slurm_max_num_timeout=30)
executor.update_parameters(
    mem_gb=5,
    gpus_per_task=1,
    tasks_per_node=1,  # one task per GPU
    cpus_per_gpu=1,
    nodes=1,
    timeout_min=500,  # max is 60 * 72
    # Below are cluster dependent parameters
    #slurm_exclude="aimagelab-srv-10",
    slurm_partition="prod",
    slurm_signal_delay_s=180,
    slurm_array_parallelism=20)
executor.update_parameters(name="dasmil")

# Read properties from CSV
df = pd.read_csv(args.propertiescsv)

# Create a list of arguments for each job
args = [args for i in range(0, len(df), args.step)]
# Submit jobs using map_array method
jobs = executor.map_array(processSlide, range(0, len(df), args[0].step), args)
# processSlide(0,args[0])
