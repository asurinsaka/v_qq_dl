from v_qq_dl.download import ProgressBar, _progress
import os

# def setup_module(ProgressBar):
#     print("============test common setup==============")
#
#
# def teardown_module(ProgressBar):
#     print("============test common teardown==============")
#
#
# def test_em():
#     print("test emß")


def test_progressbar():
    progress_bar = ProgressBar(40)
    progress_bar.update(0)
    print(progress_bar)

    progress_bar.update(.4)
    print(progress_bar)
    progress_bar.update(.4)
    print(progress_bar)
    progress_bar.update(.9)
    print(progress_bar)
    progress_bar.update(.99)
    print(progress_bar)
    progress_bar.update(1)
    print(progress_bar)
    assert str(progress_bar) == '[----------------------------------------]	100.00%'


def test_progress():
    files = []
    sizes = []
    sizes1 = []
    for i in range(5):
        files.append('test{}'.format(i))
        sizes.append(4)
        sizes1.append(8)
    for file in files:
        with open(file, 'w') as fp:
            fp.write('test')

    _progress(files, sizes, None)
    # _progress(files, sizes1, None)

    for file in files:
        if os.path.isfile(file):
            print(os.path.getsize(file))
            os.remove(file)
