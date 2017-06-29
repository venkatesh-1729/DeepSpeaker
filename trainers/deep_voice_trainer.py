import logging
import os
import time

import tensorflow as tf
from keras.callbacks import TensorBoard
from keras.losses import categorical_crossentropy
from keras.metrics import categorical_accuracy
from keras.optimizers import Adam

from data_generators.timit_data_generator import BaseBatchGenerator
from models.deep_voice_speaker_model import deep_voice_speaker_model
from utils.utils import mkdir, LoggingCallback, SaverCallback


def train(inp_shape, train_batch_generator, val_batch_generator=None,
          init_lr=0.001, epochs=1000, steps_per_epoch=20, val_steps=20, workers=4, runs_dir=None, **kwargs):
    if runs_dir is None:
        runs_dir = 'deep_voice_' + str(int(time.time()))
    model = deep_voice_speaker_model(inp_shape, **kwargs)
    opt = Adam(lr=init_lr)
    model.compile(optimizer=opt, loss=categorical_crossentropy, metrics=[categorical_accuracy])
    logging.info(model.summary())
    tb_callback = TensorBoard(log_dir=os.path.join(runs_dir, 'logs'), write_images=True)
    lc = LoggingCallback()
    sc = SaverCallback(saver=tf.train.Saver(max_to_keep=10, keep_checkpoint_every_n_hours=0.5), save_path=runs_dir,
                       model=model, name='deep_voice_cnn')
    model.fit_generator(train_batch_generator, steps_per_epoch=steps_per_epoch,
                        epochs=epochs, workers=workers, callbacks=[tb_callback, lc, sc],
                        validation_data=val_batch_generator, validation_steps=val_steps)


def main(_):
    # mkdir(os.path.join(FLAGS.runs_path, "training-log.txt"))
    # logging.basicConfig(level=logging.INFO, filename=os.path.join(FLAGS.runs_path, "training-log.txt"))
    logging.basicConfig(level=logging.INFO)

    """
    paper : Deep Voice 2: Multi-Speaker Neural Text-to-SpeechA
    focus : Speaker Discriminative Model
    url   : https://arxiv.org/pdf/1705.08947.pdf
    """

    num_speakers = FLAGS.num_speakers
    data_gen = BaseBatchGenerator(FLAGS.data_path, num_speakers=num_speakers, frames=FLAGS.frames, file_batch_size=1)
    train(inp_shape=(data_gen.frames, data_gen.dim, 1), train_batch_generator=data_gen.generator('train'),
          num_speakers=num_speakers, conv_rep=FLAGS.conv_rep, dropout=0.0, steps_per_epoch=4,
          val_batch_generator=data_gen.generator('dev'), val_steps=2)


if __name__ == '__main__':
    flags = tf.app.flags
    FLAGS = flags.FLAGS
    flags.DEFINE_string('runs_path', "", 'Runs path for tensorboard')
    flags.DEFINE_string('data_path', "", 'Dataset path')
    flags.DEFINE_integer('num_speakers', 20, 'Number of speakers')
    flags.DEFINE_integer('frames', 64, 'Number of frames')
    flags.DEFINE_integer('conv_rep', 2, 'Number of conv layers')
    tf.app.run()

