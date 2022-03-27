import torch

from multi_part_assembly.models import BaseModel
from multi_part_assembly.models import build_encoder, StocasticPoseRegressor

from .seq2seq import Seq2Seq


class LSTMModel(BaseModel):
    """Bi-LSTM based multi-part assembly model (`B-LSTM`).

    Encoder: PointNet extracting global & part point cloud feature
    Seq2seq: Bi-LSTM reasoning model
    Predictor: MLP-based pose predictor
    """

    def __init__(self, cfg):
        super().__init__(cfg)

        self.cfg = cfg

        self.max_num_part = self.cfg.data.max_num_part
        self.pc_feat_dim = self.cfg.model.pc_feat_dim

        # loss configs
        self.sample_iter = self.cfg.loss.sample_iter

        self.encoder = self._init_encoder()
        self.seq2seq = self._init_seq2seq()
        self.pose_predictor = self._init_pose_predictor()

    def _init_encoder(self):
        """Part point cloud encoder."""
        encoder = build_encoder(
            self.cfg.model.encoder,
            feat_dim=self.pc_feat_dim,
            global_feat=True,
        )
        return encoder

    def _init_seq2seq(self):
        """Bi-LSTM seq2seq module."""
        seq2seq = Seq2Seq(self.pc_feat_dim, self.pc_feat_dim,
                          self.cfg.model.lstm_hidden_size)
        return seq2seq

    def _init_pose_predictor(self):
        """Final pose estimator."""
        # concat part feature, instance_label and noise as input
        pose_predictor = StocasticPoseRegressor(
            feat_dim=self.pc_feat_dim + self.max_num_part,
            noise_dim=self.cfg.model.noise_dim,
        )
        return pose_predictor

    def _extract_part_feats(self, part_pcs, part_valids):
        """Extract per-part point cloud features."""
        B, P, N, _ = part_pcs.shape  # [B, P, N, 3]
        valid_mask = (part_valids == 1)
        # shared-weight encoder
        valid_pcs = part_pcs[valid_mask]  # [n, N, 3]
        valid_feats = self.encoder(valid_pcs)  # [n, C]
        pc_feats = torch.zeros(B, P, self.pc_feat_dim).type_as(valid_feats)
        pc_feats[valid_mask] = valid_feats
        return pc_feats

    def forward(self, data_dict):
        """Forward pass to predict poses for each part.

        Args:
            data_dict shoud contains:
                - part_pcs: [B, P, N, 3]
                - part_valids: [B, P], 1 are valid parts, 0 are padded parts
                - instance_label: [B, P, P]
            may contains:
                - pre_pose_feats: [B, P, C'] (reused) or None
        """
        feats = data_dict.get('pre_pose_feats', None)

        if feats is None:
            part_pcs = data_dict['part_pcs']
            part_valids = data_dict['part_valids']
            inst_label = data_dict['instance_label']
            pc_feats = self._extract_part_feats(part_pcs, part_valids)
            # prepare seq2seq input
            pc_feats_seq = pc_feats.transpose(0, 1).contiguous()  # [P, B, C]
            target_seq = pc_feats_seq.detach()
            output_seq, _ = self.seq2seq(pc_feats_seq, target_seq)
            output_seq = output_seq.squeeze(2).transpose(0, 1)  # [B, P, C']
            # MLP predict poses
            inst_label = inst_label.type_as(pc_feats)
            feats = torch.cat([output_seq, inst_label], dim=-1)
        quat, trans = self.pose_predictor(feats)

        pred_dict = {
            'quat': quat,  # [B, P, 4]
            'trans': trans,  # [B, P, 3]
            'pre_pose_feats': feats,  # [B, P, C']
        }
        return pred_dict

    def _loss_function(self, data_dict, out_dict={}, optimizer_idx=-1):
        """Predict poses and calculate loss.

        Since there could be several parts that are the same in one shape, we
            need to do Hungarian matching to find the min loss values.

        Args:
            data_dict: the data loaded from dataloader
            pre_pose_feats: because the stochasticity is only in the final pose
                regressor, we can reuse all the computed features before

        Returns a dict of loss, each is a [B] shape tensor for later selection.
        See GNN Assembly paper Sec 3.4, the MoN loss is sampling prediction
            several times and select the min one as final loss.
            Also returns computed features before pose regressing for reusing.
        """
        part_pcs, valids = data_dict['part_pcs'], data_dict['part_valids']
        instance_label = data_dict['instance_label']
        forward_dict = {
            'part_pcs': part_pcs,
            'part_valids': valids,
            'instance_label': instance_label,
            'pre_pose_feats': out_dict.get('pre_pose_feats', None),
        }

        # prediction
        out_dict = self.forward(forward_dict)
        pre_pose_feats = out_dict['pre_pose_feats']

        # loss computation
        loss_dict, out_dict = self._calc_loss(out_dict, data_dict)
        out_dict['pre_pose_feats'] = pre_pose_feats

        return loss_dict, out_dict