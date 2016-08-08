STYLE=$0
DATA_DIR="/root/doodle/"
STYLE_IMAGE="$DATA_DIR/$STYLE.jpg"
STYLE_MASK="$DATA_DIR/$STYLE-mask.png"
OUT="/root/data/data/$STYLE_gen_doodles.hdf5"

python generate.py --n_jobs 10 --n_colors 7 --style_image $STYLE_IMAGE --style_mask $STYLE_MASK --out_hdf5 $OUT
CUDA_VISIBLE_DEVICES=0 th feedforward_neural_doodle.lua -model_name skip_noise_4 -masks_hdf5 $OUT -batch_size 1 -num_mask_noise_times 0 -num_noise_channels 0 -learning_rate 1e-1 -half false

mv data/out/model.t7 $DATA_DIR/model.t7
rm -f $OUT

