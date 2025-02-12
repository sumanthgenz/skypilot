import subprocess

import sky

with sky.Dag() as dag:
    # The working directory contains all code and will be synced to remote.
    workdir = '~/Downloads/tpu'
    subprocess.run(f'cd {workdir} && git checkout 222cc86',
                   shell=True,
                   check=True)

    # The setup command.  Will be run under the working directory.
    setup = 'pip install --upgrade pip && \
        conda init bash && \
        conda activate resnet || \
          (conda create -n resnet python=3.7 -y && \
           conda activate resnet && \
           conda install cudatoolkit=11.0 -y && \
           pip install tensorflow==2.4.0 pyyaml && \
           pip install protobuf==3.20 && \
           cd models && pip install -e .)'

    # The command to run.  Will be run under the working directory.
    run = 'conda activate resnet && \
        export XLA_FLAGS=\'--xla_gpu_cuda_data_dir=/usr/local/cuda/\' && \
        python -u models/official/resnet/resnet_main.py --use_tpu=False \
        --mode=train --train_batch_size=256 --train_steps=250 \
        --iterations_per_loop=125 \
        --data_dir=gs://cloud-tpu-test-datasets/fake_imagenet \
        --model_dir=resnet-model-dir \
        --amp --xla --loss_scale=128'

    ### Optional: download data to VM's local disks. ###
    # Format: {VM paths: local paths / cloud URLs}.
    file_mounts = {
        # Download from GCS before training starts.
        # '/tmp/fake_imagenet': 'gs://cloud-tpu-test-datasets/fake_imagenet',
    }
    # Refer to the VM local path.
    # run = run.replace('gs://cloud-tpu-test-datasets/fake_imagenet',
    #                   '/tmp/fake_imagenet')
    ### Optional end ###

    train = sky.Task(
        'train',
        workdir=workdir,
        setup=setup,
        run=run,
    )
    train.set_file_mounts(file_mounts)
    # TODO: allow option to say (or detect) no download/egress cost.
    train.set_inputs('gs://cloud-tpu-test-datasets/fake_imagenet',
                     estimated_size_gigabytes=70)
    train.set_outputs('resnet-model-dir', estimated_size_gigabytes=0.1)
    train.set_resources({
        ##### Fully specified
        # sky.Resources(sky.AWS(), 'p3.2xlarge'),
        # sky.Resources(sky.GCP(), 'n1-standard-16'),
        # sky.Resources(
        #     sky.GCP(),
        #     'n1-standard-8',
        #     # Options: 'V100', {'V100': <num>}.
        #     'V100',
        # ),
        ##### Partially specified
        # sky.Resources(accelerators='T4'),
        # sky.Resources(accelerators={'T4': 8}, use_spot=True),
        # sky.Resources(sky.AWS(), accelerators={'T4': 8}, use_spot=True),
        # sky.Resources(sky.AWS(), accelerators='K80'),
        # sky.Resources(sky.AWS(), accelerators='K80', use_spot=True),
        # sky.Resources(accelerators='tpu-v3-8'),
        # sky.Resources(accelerators='V100', use_spot=True),
        # sky.Resources(accelerators={'T4': 4}),
        sky.Resources(sky.AWS(), accelerators='V100'),
        # sky.Resources(sky.GCP(), accelerators={'V100': 4}),
        # sky.Resources(sky.AWS(), accelerators='V100', use_spot=True),
        # sky.Resources(sky.AWS(), accelerators={'V100': 8}),
    })

    # Optionally, specify a time estimator: Resources -> time in seconds.
    # train.set_time_estimator(time_estimators.resnet50_estimate_runtime)

# sky.launch(dag, dryrun=True)
sky.launch(dag)
