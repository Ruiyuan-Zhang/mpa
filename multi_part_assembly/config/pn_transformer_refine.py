from yacs.config import CfgNode as CN

# Miscellaneous configs
_C = CN()

# Experiment related
_C.exp = CN()
_C.exp.name = 'pn_transformer_refine'
_C.exp.ckp_dir = 'checkpoint/'
_C.exp.weight_file = ''
_C.exp.gpus = [
    0,
]
_C.exp.num_workers = 4
_C.exp.batch_size = 32
_C.exp.num_epochs = 400
_C.exp.val_every = 5  # evaluate model every n training epochs
_C.exp.val_sample_vis = 5  # sample visualizations

# Model related
_C.model = CN()
_C.model.refine_steps = 3
_C.model.encoder = 'pointnet'  # 'dgcnn', 'pointnet2_ssg', 'pointnet2_msg'
_C.model.pc_feat_dim = 128
_C.model.transformer_pos_enc = (7, 128, 128)
_C.model.transformer_feat_dim = 512
_C.model.transformer_heads = 8
_C.model.transformer_layers = 2
_C.model.transformer_pre_ln = True
_C.model.noise_dim = 32  # stochastic PoseRegressor
_C.model.pose_pc_feat = True  # pose regressor input part points feature
_C.model.global_feat = False  # global shape feature as Transformer input
_C.model.num_global_pts = 1024

# Loss related
# default setting follows GNN paper, use L2 trans loss, CD of rotated parts and
# CD of transformed whole shapes
_C.loss = CN()
_C.loss.sample_iter = 5  # MoN loss sampling
# the best loss settings for baseline after some ablation
#   - translation l2 with weight = 1
#   - rotated part points chamfer with weight = 10
#   - transformed whole shape points chamfer with weight = 10
#   - not using direct loss on rotation angle, l2 loss on rotated points
#       because there is no clear point correspondence here given the symmetry
#       of parts, and many parts are extremely similar to each other
_C.loss.trans_loss_w = 1.
_C.loss.rot_pt_cd_loss_w = 10.
_C.loss.transform_pt_cd_loss_w = 10.

# Data related
_C.data = CN()
_C.data.data_dir = '../Generative-3D-Part-Assembly/prepare_data'
_C.data.data_fn = 'Chair.{}.npy'
_C.data.data_keys = ('part_ids', 'instance_label', 'match_ids',
                     'contact_points')
_C.data.num_pc_points = 1000  # points per part
_C.data.max_num_part = 20
_C.data.overfit = -1
_C.data.pad_points = 0.
_C.data.colors = [
    [0, 204, 0],
    [204, 0, 0],
    [0, 204, 0],
    [127, 127, 0],
    [127, 0, 127],
    [0, 127, 127],
    [76, 153, 0],
    [153, 0, 76],
    [76, 0, 153],
    [153, 76, 0],
    [76, 0, 153],
    [153, 0, 76],
    [204, 51, 127],
    [204, 51, 127],
    [51, 204, 127],
    [51, 127, 204],
    [127, 51, 204],
    [127, 204, 51],
    [76, 76, 178],
    [76, 178, 76],
    [178, 76, 76],
]

# Optimizer related
_C.optimizer = CN()
_C.optimizer.lr = 1e-3
_C.optimizer.weight_decay = 0.
_C.optimizer.warmup_ratio = 0.05
_C.optimizer.clip_grad = None


def get_cfg_defaults():
    return _C.clone()