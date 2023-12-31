seed = 42
scale = 4
# model settings
model = dict(
    type='BasicRestorer',
    generator=dict(
        type='MSRResNet',
        in_channels=3,
        out_channels=3,
        mid_channels=64,
        num_blocks=16,
        upscale_factor=scale),
    pixel_loss=dict(type='L1Loss', loss_weight=1.0, reduction='mean'))
# model training and testing settings
train_cfg = None
test_cfg = dict(metrics=['PSNR', 'SSIM'], crop_border=0)

# dataset settings
train_dataset_type = 'SRFolderDataset'
val_dataset_type = 'SRFolderDataset'
train_pipeline = [
    dict(
        type='LoadImageFromFile',
        io_backend='disk',
        key='gt',
        channel_order='rgb'),
    dict(type='RescaleToZeroOne', keys=['gt']),
    dict(type='CopyValues', src_keys=['gt'], dst_keys=['lq']),
    dict(
        type='RandomBlur',
        params=dict(
            kernel_size=[41],
            kernel_list=['iso', 'aniso'],
            kernel_prob=[0.5, 0.5],
            sigma_x=[0.2, 5],
            sigma_y=[0.2, 5],
            rotate_angle=[-3.1416, 3.1416],
        ),
        keys=['lq'],
    ),
    dict(
        type='RandomResize',
        params=dict(
            resize_mode_prob=[0, 1, 0],  # up, down, keep
            resize_scale=[0.0625, 1],
            resize_opt=['bilinear', 'area', 'bicubic'],
            resize_prob=[1 / 3., 1 / 3., 1 / 3.]),
        keys=['lq'],
    ),
    dict(
        type='RandomNoise',
        params=dict(
            noise_type=['gaussian'],
            noise_prob=[1],
            gaussian_sigma=[0, 25],
            gaussian_gray_noise_prob=0),
        keys=['lq'],
    ),
    dict(
        type='RandomJPEGCompression',
        params=dict(quality=[50, 95]),
        keys=['lq']),
    dict(
        type='RandomResize',
        params=dict(
            target_size=(512, 512),
            resize_opt=['bilinear', 'area', 'bicubic'],
            resize_prob=[1 / 3., 1 / 3., 1 / 3.]),
        keys=['lq'],
    ),
    dict(type='Quantize', keys=['lq']),
    dict(
        type='RandomResize',
        params=dict(
            target_size=(128, 128), resize_opt=['area'], resize_prob=[1]),
        keys=['lq'],
    ),
    dict(
        type='Flip', keys=['lq', 'gt'], flip_ratio=0.5,
        direction='horizontal'),
    dict(type='ImageToTensor', keys=['lq', 'gt']),
    dict(type='Collect', keys=['lq', 'gt'], meta_keys=['gt_path'])
]

test_pipeline = [
    dict(
        type='LoadImageFromFile',
        io_backend='disk',
        key='lq',
        channel_order='rgb'),
    dict(
        type='LoadImageFromFile',
        io_backend='disk',
        key='gt',
        channel_order='rgb'),
    dict(type='RescaleToZeroOne', keys=['lq', 'gt']),
    dict(type='ImageToTensor', keys=['lq', 'gt']),
    dict(type='Collect', keys=['lq', 'gt'], meta_keys=['lq_path', 'lq_path'])
]

data = dict(
    workers_per_gpu=8,
    train_dataloader=dict(
        samples_per_gpu=8, drop_last=True, persistent_workers=False),
    val_dataloader=dict(samples_per_gpu=1, persistent_workers=False),
    test_dataloader=dict(samples_per_gpu=1, persistent_workers=False),
    train=dict(
        type='RepeatDataset',
        times=1000,
        dataset=dict(
            type=train_dataset_type,
            lq_folder='../data/train/GT',
            gt_folder='../data/train/GT',
            pipeline=train_pipeline,
            scale=scale)),
    val=dict(
        type=val_dataset_type,
        lq_folder='../data/val/LQ',
        gt_folder='../data/val/GT',
        pipeline=test_pipeline,
        scale=scale,
        filename_tmpl='{}'),
    test=dict(
        type=val_dataset_type,
        lq_folder='../data/test/LQ',
        gt_folder='../data/val/GT',
        pipeline=test_pipeline,
        scale=scale,
        filename_tmpl='{}'))

# optimizer
optimizers = dict(generator=dict(type='Adam', lr=2e-4, betas=(0.9, 0.999)))

# learning policy
total_iters = 300000
lr_config = dict(
    policy='CosineRestart',
    by_epoch=False,
    periods=[150000, 150000],
    restart_weights=[1, 1],
    min_lr=1e-7)

checkpoint_config = dict(interval=5000, save_optimizer=True, by_epoch=False)
evaluation = dict(interval=5000, save_image=False)
log_config = dict(
    interval=100,
    hooks=[
        dict(type='TextLoggerHook', by_epoch=False),
        dict(type='TensorboardLoggerHook'),
    ])
visual_config = None

# runtime settings
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = '../result/600k.py/iter_300000.pth'
resume_from = None
workflow = [('train', 1)]