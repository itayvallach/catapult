# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Helper function to run the benchmark.
"""
import os
import shutil
import subprocess

from long_term_health import utils
from long_term_health.apk_finder import ChromeVersion


SWARMING_URL = 'https://chrome-swarming.appspot.com'
ISOLATE_URL = 'https://chrome-isolated.appspot.com'

CATAPULT_ROOT = os.path.normpath(os.path.join(utils.APP_ROOT, '..', '..'))
CHROMIUM_ROOT = os.path.normpath(os.path.join(CATAPULT_ROOT, '..', '..'))
MB = os.path.join(CHROMIUM_ROOT, 'tools', 'mb', 'mb.py')
SWARMING_CLIENT = os.path.join(CHROMIUM_ROOT, 'tools', 'swarming_client')
ISOLATE = os.path.join(SWARMING_CLIENT, 'isolate.py')
PATH_TO_APKS = os.path.join(CHROMIUM_ROOT, 'tools', 'perf', 'swarming_apk')


def IncludeAPKInIsolate(apk_path):
  apk_name = os.path.basename(apk_path)
  if not os.path.isdir(PATH_TO_APKS):
    os.mkdir(PATH_TO_APKS)
  shutil.copyfile(apk_path, os.path.join(PATH_TO_APKS, apk_name))
  # relative path to be used when starting swarming job
  return os.path.join('..', '..', 'tools', 'perf', 'swarming_apk', apk_name)


def GenerateIsolate(out_dir_path, target_name):
  # TODO(wangge): need to make it work even if there is no `out/Debug`
  subprocess.call([MB, 'isolate', out_dir_path, target_name])


def UploadIsolate(isolated_path):
  return subprocess.check_output(
      [ISOLATE, 'archive', '-I', ISOLATE_URL, '-s', isolated_path])


def RunBenchmark(path_to_apk, run_label):
  """Install the APK and run the benchmark on it.

  Args:
    path_to_apk(string): the *relative* path to the APK
    run_label(string): the name of the directory to contains all the output
    from this run
  """
  # `path_to_apk` is similar to `./out/59.0.3071.132_arm_MonochromeStable.apk`
  chrome_version = ChromeVersion(path_to_apk.split('/')[-1].split('_')[0])
  subprocess.call(['adb', 'install', '-r', '-d', path_to_apk])
  subprocess.call([os.path.join(utils.CHROMIUM_SRC, 'tools',
                                'perf', 'run_benchmark'),
                   '--browser=android-system-chrome',
                   '--pageset-repeat=1',  # could remove this later
                   '--results-label=%s' % str(chrome_version),
                   # TODO(wangge):not sure if we should run in compatibility
                   # mode even for the later version, probably add a check in
                   # caller to determine if we should run it in compatibility
                   # mode and add an argument `run_in_compatibility_mode` to
                   # the `RunBenchmark` function
                   '--compatibility-mode=no-field-trials',
                   '--compatibility-mode=ignore-certificate-errors',
                   '--compatibility-mode=legacy-command-line-path',
                   '--compatibility-mode=gpu-benchmarking-fallbacks',
                   '--story-filter=wikipedia',  # could remove this
                   # thinking of adding an argument to the tool to set this
                   '--output-dir=%s' % os.path.join(
                       utils.APP_ROOT, 'results', run_label,
                       str(chrome_version.milestone)),
                   # thinking of adding an argument to the tool to set this too
                   'system_health.memory_mobile'])
