'''
Simulation-running and -plotting thread/worker functions.
Based on SimRun model. Updates django db and is implemented as a django command.
Outputs comprehensive messages to stdout, which can be increased to include
mcrun, mcdisplay and mcplot stdout and stderr.
'''
import json
import getpass
import subprocess
import os
import sys
import time
import tarfile
import threading
import logging
import re
import traceback
import pyparsing
import yaml

from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone
from simrunner.models import SimRun
from mcweb.settings import STATIC_URL, SIM_DIR, DATA_DIRNAME, MCRUN_OUTPUT_DIRNAME, MCPLOT_CMD, MCPLOT_LOGCMD, MCPLOT_USE_HTML_PLOTTER
from mcweb.settings import MPI_PR_WORKER, MAX_THREADS, MCRUN, MXRUN, BASE_DIR
import mcweb.settings as settings
from simrunner.generate_static import McStaticDataBrowserGenerator

class ExitException(Exception):
    ''' used to signal a runworker shutdown, rather than a simrun object fail-time and -string '''
    pass

def maketar(simrun):
    ''' makes the tar-file for download from the status page '''
    try:
        with tarfile.open(os.path.join(simrun.data_folder, 'simrun.tar.gz'), "w:gz") as tar:
            tar.add(simrun.data_folder, arcname=os.path.basename(simrun.data_folder))
    except:
        raise Exception('tarfile fail')

def plot_file(f, log=False):
    cmd = '%s %s' % (MCPLOT_CMD, f)
    if log:
        cmd = '%s %s' % (MCPLOT_LOGCMD,f)
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    (stdoutdata, stderrdata) = process.communicate()
    if os.path.isfile( f + '.png'):
        if log:
            os.rename(f + '.png',os.path.splitext(os.path.splitext(f)[0])[0] + '_log.png')
        else:
            os.rename(f + '.png',os.path.splitext(os.path.splitext(f)[0])[0] + '.png')

    return (stdoutdata, stderrdata)

def sweep_zip_gen(f,dirname):
    ''' generate monitor zip file in sweep case '''
    p = os.path.basename(f)
    p_zip = os.path.splitext(p)[0] + '.zip'

    _log('sweep_zip_gen: %s in %s ' % (p, dirname))

    cmd = 'find mcstas/ -name ' + p + '| sort -V | xargs zip -r ' + p_zip
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
	                       shell=True, cwd=dirname)
    (stdoutdata, stderrdata) = process.communicate()
    _log(stdoutdata)
    _log(stderrdata)
    return (stdoutdata, stderrdata)

def rename_mcstas_to_mccode(simrun):
    ''' run before mcplot to avoid issues with old versions of mcstas '''
    for token in ['.sim', '.dat']:
        wrong = os.path.join(simrun.data_folder, 'mcstas%s' % token)
        right = os.path.join(simrun.data_folder, 'mccode%s' % token)
        if os.path.exists(wrong):
            os.rename(wrong, right)

def get_monitor_files(mccode_sim):
    ''' implements "data files can have any name" '''
    monitor_files = filter(lambda line: (line.strip()).startswith('filename:'), open(mccode_sim).readlines())
    monitor_files = map(lambda f: f.rstrip('\n').split(':')[1].strip(), monitor_files)
    return monitor_files

def mcplot(simrun):
    ''' generates plots from simrun output data '''
    ''' also spawns monitor zip file creation in case of scan sweep '''
    rename_mcstas_to_mccode(simrun)
    plotfiles_ext = "html" if MCPLOT_USE_HTML_PLOTTER else "png"

    try:
        if simrun.scanpoints > 1:
            # init
            plot_files = []
            plot_files_log = []
            data_files = []

            # plot and store mccode.dat, which must exist
            f = os.path.join(simrun.data_folder, MCRUN_OUTPUT_DIRNAME, 'mccode.dat')

            plot_file(f)
            p = os.path.basename(f)
            p = os.path.splitext(p)[0] + '.' + plotfiles_ext
            p = os.path.join(MCRUN_OUTPUT_DIRNAME, p)
            plot_files.append(p)

            plot_file(f, log=True)
            p_log = os.path.basename(f)
            p_log = os.path.splitext(p_log)[0] + '.' + plotfiles_ext
            p_log = os.path.join(MCRUN_OUTPUT_DIRNAME, p_log)
            plot_files_log.append(p_log)

            d = os.path.basename(f)
            d = os.path.join(MCRUN_OUTPUT_DIRNAME, d)
            data_files.append(d)

            _log('plot_linlog: %s' % p)

            for i in range(simrun.scanpoints):
                if i > 0:
                    _log('plot_linlog (scanpoint index %d)...' % i)

                outdir = os.path.join(simrun.data_folder, MCRUN_OUTPUT_DIRNAME, str(i))

                datfiles_nodir = get_monitor_files(os.path.join(outdir, 'mccode.sim'))
                datfiles = map(lambda f: os.path.join(outdir, f), datfiles_nodir)

                for f in datfiles:
                    plot_file(f)
                    plot_file(f, log=True)

                    p = os.path.basename(f)
                    p = os.path.splitext(p)[0] + '.' + plotfiles_ext
                    p = os.path.join(MCRUN_OUTPUT_DIRNAME, str(i), p)

                    p_log = os.path.basename(f)
                    p_log = os.path.splitext(p_log)[0] + '.' + plotfiles_ext
                    p_log = os.path.join(MCRUN_OUTPUT_DIRNAME, str(i), p_log)

                    d = os.path.basename(f)
                    d = os.path.join(MCRUN_OUTPUT_DIRNAME, str(i), d)

                    if i == 0:
                        _log('plot_linlog: %s' % p)
                        plot_files.append(p)
                        plot_files_log.append(p_log)
                        data_files.append(d)
            for f in datfiles:
                sweep_zip_gen(f,simrun.data_folder)

        else:
            outdir = os.path.join(simrun.data_folder, MCRUN_OUTPUT_DIRNAME)

            datfiles_nodir = get_monitor_files(os.path.join(outdir, 'mccode.sim'))
            datfiles = map(lambda f: os.path.join(outdir, f), datfiles_nodir)

            data_files = []
            plot_files = []
            plot_files_log = []

            for f in datfiles:
                plot_file(f)

                p = os.path.basename(f)
                p = os.path.splitext(p)[0] + '.' + plotfiles_ext
                p = os.path.join(MCRUN_OUTPUT_DIRNAME, p)

                _log('plot: %s' % p)
                plot_files.append(p)

            # NOTE: the following only works with mcplot-gnuplot-py
            for f in datfiles:
                plot_file(f, log=True)

                l = os.path.basename(f)
                l = os.path.splitext(l)[0] + '_log.' + plotfiles_ext
                l = os.path.join(MCRUN_OUTPUT_DIRNAME, l)

                _log('plot: %s' % l)
                plot_files_log.append(l)

            for f in datfiles:
                d = os.path.basename(f)
                d = os.path.join(MCRUN_OUTPUT_DIRNAME, d)

                data_files.append(d)

        simrun.data_files = data_files
        simrun.plot_files = plot_files
        simrun.plot_files_log = plot_files_log
        simrun.save()

    except Exception as e:
        raise Exception('mcplot fail: %s' % e.__str__())

def mcdisplay_webgl(simrun, pout=False):
    ''' apply mcdisplay-webgl output to subfolder 'mcdisplay', renaming index.html to mcdisplay.html '''
    join = os.path.join

    dirname = 'mcdisplay'
    instr = '%s.instr' % simrun.instr_displayname

    MCCODE = settings.MCDISPLAY_WEBGL

    instr_file = 'sim/' + simrun.group_name + '/' + instr

    # Remove this for now, generates OOM errors
    # # Check if this is McStas or McXtrace by a simple
    # for line in open(instr_file):
    #     if re.search('mcxtrace', line, re.IGNORECASE):
    #         MCCODE = settings.MXDISPLAY_WEBGL
    #         break

    params_str_lst = []
    for p in simrun.params:
        # scan sweep special case - use last scanpoint
        m = re.search(',\s*([0-9\.]+)', p[1])
        if m:
            p[1] = m.group(1)
        params_str_lst.append('%s=%s' % (p[0], p[1]))
    params_str = ' '.join(params_str_lst)
    cmd = '%s %s %s --nobrowse --dir=%s' % (MCCODE, instr, params_str, dirname)

    # TODO: inplement --inspect, --first, --last

    # run mcdisplay
    _log('display_webgl: %s' % cmd)
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True,
                               cwd = os.path.join(BASE_DIR, simrun.data_folder))
    (stdoutdata, stderrdata) = process.communicate()
    if pout:
        print(stdoutdata)
        if (stderrdata is not None) and (stderrdata != ''):
            print(stderrdata)

    # copy files
    #_log('mcdisplay: renaming index.html')
    #os.rename(join(simrun.data_folder, dirname, 'index.html'), join(simrun.data_folder, dirname, 'mcdisplay.html'))

def mcdisplay(simrun, print_mcdisplay_output=False):
    ''' uses mcdisplay to generate layout.png + VRML file and moves these files to simrun.data_folder '''
    try:
        instr = '%s.instr' % simrun.instr_displayname

        MCCODE = settings.MCDISPLAY

        instr_file = 'sim/' + simrun.group_name + '/' + instr

        # Remove this for now, generates OOM errors
        # # Check if this is McStas or McXtrace by a simple
        # for line in open(instr_file):
        #     if re.search('mcxtrace', line, re.IGNORECASE):
        #         MCCODE = settings.MXDISPLAY
        #         break

        cmd = '%s -png %s -n1 ' % (MCCODE, instr)
        vrmlcmd = '%s --format=VRML %s -n1 ' % (MCCODE, instr)

        for p in simrun.params:
            s = str(p[1])
            # support for scan sweeps; if a param contains comma, get str before (mcdisplay dont like comma)
            # (NOTE: perhaps better to make a layout.png file for every scan point)
            if ',' in s:
                s = s.split(',')[0]
            cmd = cmd + ' %s=%s' % (p[0], s)
            vrmlcmd = vrmlcmd + ' %s=%s' % (p[0], s)

        _log('display: %s' % cmd)
        _log('display_vrml: %s' % vrmlcmd)

        # start mcdisplay process, wait
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd = simrun.data_folder)
        (stdoutdata, stderrdata) = process.communicate()
        process2 = subprocess.Popen(vrmlcmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd = simrun.data_folder)
        (stdoutdata2, stderrdata2) = process2.communicate()

        if print_mcdisplay_output:
            print(stdoutdata)
            if (stderrdata is not None) and (stderrdata != ''):
                print(stderrdata)
        if print_mcdisplay_output:
            print(stdoutdata2)
            if (stderrdata2 is not None) and (stderrdata2 != ''):
                print(stderrdata2)

        oldfilename = '%s.out.png' % os.path.join(simrun.data_folder, simrun.instr_displayname)
        newfilename = os.path.join(simrun.data_folder, 'layout.png')
        oldwrlfilename = os.path.join(simrun.data_folder,'mcdisplay_commands.wrl')
        newwrlfilename = os.path.join(simrun.data_folder, 'layout.wrl')

        os.rename(oldfilename, newfilename)
        os.rename(oldwrlfilename, newwrlfilename)

        _log('layout: %s' % newfilename)
        _log('layout: %s' % newwrlfilename)

    except Exception as e:
        _log('mcdisplay fail: %s \nwith stderr:      %s \n     stderr_wrml: %s' % (e.__str__(), stderrdata, stderrdata2))

def mcrun(simrun):
    ''' runs the simulation associated with simrun '''

    MCCODE = identify_run_type(simrun)

    # assemble the run command
    gravity = '-g ' if simrun.gravity else ''
    runstr = MCCODE + ' --mpi=' + str(MPI_PR_WORKER) + " " + gravity + simrun.instr_displayname + '.instr -d ' + MCRUN_OUTPUT_DIRNAME
    runstr = runstr + ' -n ' + str(simrun.neutrons)
    if simrun.scanpoints > 1:
        runstr = runstr + ' -N ' + str(simrun.scanpoints)
    if simrun.seed > 0:
        runstr = runstr + ' -s ' + str(simrun.seed)
    for p in simrun.params:
        runstr = runstr + ' ' + p[0] + '=' + p[1]

    # create empty stdout.txt and stderr.txt files
    f = open('%s/stdout.txt' % simrun.data_folder, 'w')
    f.write("no stdout data for: %s" % runstr)
    f.close()
    f = open('%s/stderr.txt' % simrun.data_folder, 'w')
    f.write("no stderr data for: %s" % runstr)
    f.close()

    _log('running: %s...' % runstr)
    process = subprocess.Popen(runstr,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True,
                               cwd=simrun.data_folder)
    # TODO: implement a timeout (max simulation time)
    (stdout, stderr) = process.communicate()

    o = open('%s/stdout.txt' % simrun.data_folder, 'w')
    o.write(stdout)
    o.close()
    e = open('%s/stderr.txt' % simrun.data_folder, 'w')
    e.write(stderr)
    e.close()

    if process.returncode != 0:
        raise Exception('Instrument run failure - see %s.' % simrun.data_folder )

    _log('data: %s' % simrun.data_folder)

def remote_mcrun(simrun):
    '''
    runs the simulation associated with simrun
    '''

    MCCODE = identify_run_type(simrun)

    # create empty stdout.txt and stderr.txt files
    f = open('%s/stdout.txt' % simrun.data_folder, 'w+')
    f.close()
    f = open('%s/stderr.txt' % simrun.data_folder, 'w+')
    f.close()

    environment_vars = os.environ
    try:
        cmd_args = [MCCODE]
        cores = get_instance_cores()

        cmd_args.append('--mpi=%d' % cores)

        cmd_args.append(simrun.instr_displayname + ".instr")

        if simrun.gravity:
            cmd_args.append('-g')

        cmd_args.extend(['-d', '/tmp/output'])
        cmd_args.extend(['-n', str(simrun.neutrons)])
        if simrun.scanpoints > 1:
            cmd_args.extend(['-N', str(simrun.scanpoints)])
        if simrun.seed > 0:
            cmd_args.extend(['-s', str(simrun.seed)])
        for p in simrun.params:
            cmd_args.append(p[0] + '=' + p[1])

        # _log('command args are: %s' % cmd_args)

        absolute_data_path = os.path.join(os.getcwd(), simrun.data_folder)

        runstr = "corc oci job run " \
                 + '\'' + ' '.join(cmd_args) + '\'' \
                 + " --storage-enable" \
                 + " --storage-upload-path " \
                 + absolute_data_path \
                 + " --job-working-dir " \
                 + '/tmp/input'
        _log('job runstr is: %s' % runstr)

        process = subprocess.Popen(runstr,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=simrun.data_folder)

        (stdout, stderr) = process.communicate()

        o = open('%s/stdout.txt' % simrun.data_folder, 'w')
        o.write(stdout)
        o.close()
        e = open('%s/stderr.txt' % simrun.data_folder, 'w')
        e.write(stderr)
        e.close()

        try:
            json_dict = json.loads(stdout.decode('utf-8'))
            job_id = json_dict['job']['id']
            _log("Job submitted with ID: '%s'" % job_id)

        except Exception:
            msg = "Could not retrieve job_id."
            _log(msg)
            raise Exception(msg)

        attempt = 0
        # start querying for job outputs?
        # This will loop infinitely. Put in a timeout?
        while True:
            # Log attempts and pid, so that if infinitely running should be
            # easier to debug and kill
            attempt += 1
            _log("worker running on pid(%s) is querying(%s). Attempt(%s)"
                 % (os.getpid(), job_id, attempt))
            download_path = os.path.join(os.getcwd(), simrun.data_folder)
            runstr = "corc oci job result get" \
                     + " --job-meta-name " + job_id \
                     + " --storage-download-path " + download_path
            _log('data runstr is: %s' % runstr)

            process = subprocess.Popen(runstr,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True,
                                       cwd=simrun.data_folder)

            (stdout, stderr) = process.communicate()

            if stderr:
                break

            _log('checking for output...')

            oci_output_path = ''
            dir_contents = os.listdir(simrun.data_folder)
            for content in dir_contents:
                if content.startswith(job_id):
                    oci_output_path = os.path.join(simrun.data_folder, content)

            if oci_output_path:
                _log('output exists at: %s' % oci_output_path)
                outputs = os.listdir(oci_output_path)
                _log('Got output from oci job: %s' % os.listdir(oci_output_path))
                os.mkdir(os.path.join(simrun.data_folder, MCRUN_OUTPUT_DIRNAME))
                for output in outputs:
                    src_path = os.path.join(oci_output_path, output)
                    final_path = os.path.join(simrun.data_folder, MCRUN_OUTPUT_DIRNAME, output)
                    p = subprocess.Popen(['cp', '-p', src_path, final_path])
                    p.wait()
                    _log('Copied %s to %s' % (src_path, final_path))
                break

            time.sleep(15)

        o = open('%s/stdout.txt' % simrun.data_folder, 'a')
        o.write(stdout)
        o.close()
        e = open('%s/stderr.txt' % simrun.data_folder, 'a')
        e.write(stderr)
        e.close()

        _log('Completed remote running')

    except Exception as e:
        msg = "Problem encountered whilst running remotely. %s" % e
        _log(msg)
        raise Exception(msg)

def get_instance_cores():
    # TODO update to Python3
    # Get cores on remote image. If McWeb is ever updated to use python3
    # we can update this whole section to use corc python functions
    # explictly. In the mean time this will have to do. Currently only
    # supports oci.

    try:
        runstr = 'corc oci orchestration instance list'

        process = subprocess.Popen(
            runstr,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        (stdout, stderr) = process.communicate()

        # Write instances to file
        instances_filename = 'instances'
        with open(instances_filename, 'w') as instances_file:
            instances_file.write(stdout.decode('utf-8'))

        # Get the corc config
        corc_config_path = \
            os.path.join(os.path.expanduser('~'), '.corc', 'config')

        if not os.path.exists(corc_config_path):
            _log('corc config missing at %s. Using default core value of 1'
                 % corc_config_path)
            return 1

        with open(corc_config_path, "r") as corc_config_file:
            config = yaml.safe_load(corc_config_file)

        # Get the cores of the current instance matching the defined shape
        config_shape = \
            config['corc']['providers']['oci']['cluster']['node']['node_shape']

        with open(instances_filename) as json_file:

            data = json.load(json_file)
            instances_list = data['instances']

            for instance in instances_list:
                if 'shape' in instance and instance['shape'] == config_shape:
                    cores = int(float(instance['shape_config']['ocpus']))
                    _log('Found %s cores' % cores)
                    return cores
    except Exception as exc:
        _log('Could not find number of cores due to: %s. defaulting to 1 '
             'core' % str(exc))
        return 1


def identify_run_type(simrun):
    MCCODE = MCRUN

    instr_file = 'sim/' + simrun.group_name + '/' + simrun.instr_displayname + '.instr'

    # Check if this is McStas or McXtrace by a simple
    for line in open(instr_file):
        if re.search('mcxtrace', line, re.IGNORECASE):
            MCCODE = MXRUN
            break

    if '.pl' in MCCODE:
        MCCODE = MCCODE.replace('.pl', '')

    return MCCODE

def init_processing(simrun):
    ''' creates data folder, copies instr files and updates simrun object '''
    try:
        simrun.data_folder = os.path.join(os.path.join(STATIC_URL.lstrip('/'), DATA_DIRNAME), simrun.__str__())
        os.mkdir(simrun.data_folder)
        simrun.save()

        # copy instrument from sim folder to simrun data folder
        instr_source = '%s/%s/%s.instr' % (SIM_DIR, simrun.group_name, simrun.instr_displayname)
        instr = '%s/%s.instr' % (simrun.data_folder, simrun.instr_displayname)
        p = subprocess.Popen(['cp', '-p', instr_source, instr])
        p.wait()

        # symlink the .c and the .out files
        src_c = '%s/%s/%s.c' % (SIM_DIR, simrun.group_name, simrun.instr_displayname)
        src_out = '%s/%s/%s.out' % (SIM_DIR, simrun.group_name, simrun.instr_displayname)
        ln_c = '%s/%s.c' % (simrun.data_folder, simrun.instr_displayname)
        ln_out = '%s/%s.out' % (simrun.data_folder, simrun.instr_displayname)
        p = subprocess.Popen(['cp', '-p', src_c, ln_c])
        p.wait()
        p = subprocess.Popen(['cp', '-p', src_out, ln_out])
        p.wait()

        # symlink the contents of sim/datafiles/

        allfiles = [f for f in os.listdir('sim/datafiles/') if os.path.isfile(os.path.join('sim/datafiles/', f))]
        if '.gitignore' in allfiles:
            allfiles.remove('.gitignore')
        for f in allfiles:
            src = os.path.join('..', '..', '..', 'sim', 'datafiles', f)
            ln = '%s/%s' % (simrun.data_folder, f)
            os.symlink(src, ln)

    except Exception as e:
        raise Exception('init_processing: %s (%s)' % (type(e).__name__, e.__str__()))

def gather_files(simrun):
    '''copies over all component definitions and additional data files as
    they will be needed for processing'''

    # Get relevant component files
    instr_filename = '%s/%s.instr' % (simrun.data_folder, simrun.instr_displayname)
    with open(instr_filename) as instr_file:
        instr_data = instr_file.read()

    pyparsing.cppStyleComment.ignore(pyparsing.dblQuotedString)
    stripped_instr_data = pyparsing.cppStyleComment.suppress().transformString(instr_data)

    component_token = "COMPONENT"
    component_variable = pyparsing.Word(pyparsing.alphanums + '_')('variable')
    equals = pyparsing.Suppress('=')
    component_type = pyparsing.Word(pyparsing.alphanums + '-_!#$%&*+,-/:;<=>?@^`|~')('type')

    variable_definition = component_token + component_variable + equals + component_type

    matches = variable_definition.scanString(stripped_instr_data)
    components = []
    for match in matches:
        result = match[0]
        if result.type not in components:
            components.append(result.type)

    _log('Got %s unique components' % len(components))
    _log(components)

    for component in components:
        # find files locally
        group_path = os.path.join('sim', simrun.group_name, component + '.comp')
        _log('checking local path: %s' % group_path)

        if os.path.exists(group_path):
            _log('Got local component: %s' % component)

            target_path = os.path.join(simrun.data_folder, component + '.comp')

            p = subprocess.Popen(['cp', '-p', group_path, target_path])
            p.wait()
        else:
            _log('Component %s does not exist locally, using pre-defined version' % component)

    # Copy additional data files
    extrafiles = simrun.extrafiles
    copyall = simrun.copyall
    if copyall:
        _log('Copying all additional local files.')

        source_path = os.path.join('sim', simrun.group_name)
        onlyfiles = [filename for filename in os.listdir(source_path)
                     if os.path.isfile(os.path.join(source_path, filename))
                     and not filename.endswith('.instr')
                     and not filename.endswith('.comp')]

        for filename in onlyfiles:
            target_path = os.path.join(simrun.data_folder, filename)
            p = subprocess.Popen(['cp', '-p', os.path.join(source_path, filename), target_path])
            p.wait()

        _log('Copied additional files: %s' % onlyfiles)

    elif extrafiles:
        _log('Copying defined additional files: %s' % extrafiles)

        for filename in extrafiles:
            source_path = os.path.join('sim', simrun.group_name, filename)
            target_path = os.path.join(simrun.data_folder, filename)
            if os.path.exists(source_path) and os.path.isfile(source_path):
                p = subprocess.Popen(['cp', '-p', os.path.join(source_path, filename), target_path])
                p.wait()
            else:
                _log('Could not copy file: %s' % filename)

def check_age(simrun, max_mins):
    ''' checks simrun age: raises an exception if age is greater than max_mins. (Does not alter object simrun.) '''
    age = simrun.started - simrun.created
    age_mins = age.seconds / 60
    if age_mins > max_mins:
        raise Exception('Age of object has timed out for %s running %s at time %s).' %
            (simrun.owner_username,simrun.instr_displayname ,simrun.created.strftime("%H:%M:%S_%Y-%m-%d")))

def get_and_start_new_simrun():
    ''' gets an unstarted simrun from the db, sets its status to "running" and return it. Otherwise it returns None '''
    simrun = None
    simrun_set = SimRun.objects.filter(started=None)
    if len(simrun_set) > 0:
        simrun = simrun_set[0]

        simrun.started = timezone.now()
        simrun.save()

    return simrun

def cache_check(simrun):
    '''
    Checks if a similar simrun exists and if this run is allows to be loaded from cache.
    If so, it loads the cache and returns True, and False otherwise.
    '''
    simrun_matches = SimRun.objects.filter(enable_cachefrom=True, group_name=simrun.group_name, instr_displayname=simrun.instr_displayname, params_str=simrun.params_str, gravity=simrun.gravity, scanpoints=simrun.scanpoints, neutrons__gte = simrun.neutrons).order_by('-complete')
    if len(simrun_matches) > 0:
        simrun.data_folder = os.path.join(os.path.join(STATIC_URL.lstrip('/'), DATA_DIRNAME), simrun.__str__())
        # Simple unix cp -r of data directory
        process = subprocess.Popen("cp -r " + simrun_matches[0].data_folder + " " + simrun.data_folder,
                                                                  stdout=subprocess.PIPE,
                                                                  stderr=subprocess.PIPE,
                                                                  shell=True)
        (stdout, stderr) = process.communicate()
        # Run stream editor to replace "Completed" label with "Loaded cache data from"
        process = subprocess.Popen("sed -i.bak s\"/Completed/Loaded\ cache\ data\ from/\" " + simrun.data_folder + "/browse*.html",
                                                                                                     stdout=subprocess.PIPE,
                                                                                                     stderr=subprocess.PIPE,
                                                                                                     shell=True)
        (stdout, stderr) = process.communicate()
        simrun.complete = simrun_matches[0].complete
        simrun.save()
        return True
    else:
        return False

def write_results(simrun):
    ''' Generate data browser page. '''
    lin_log_html = 'lin_log_url: impl.'
    gen = McStaticDataBrowserGenerator()
    _log("setting base context")

    date_time_completed = timezone.localtime(simrun.complete).strftime("%H:%M:%S, %d/%m-%Y")
    date_time_created = timezone.localtime(simrun.created).strftime("%H:%M:%S, %d/%m-%Y")
    date_time_started = timezone.localtime(simrun.started).strftime("%H:%M:%S, %d/%m-%Y")
    date_time_processed = timezone.localtime(simrun.processed).strftime("%H:%M:%S, %d/%m-%Y")

    total_time_taken = "(%s seconds)" % (simrun.complete - simrun.created).seconds
    delay_time = "(%s seconds)" % (simrun.started - simrun.created).seconds
    run_time = "(%s seconds)" % (simrun.complete - simrun.started).seconds
    simulation_time = "(%s seconds)" % (simrun.processed - simrun.started).seconds

    _log("Simrun timing data:")
    _log("Created at: %s" % date_time_created)
    _log("Started at: %s" % date_time_started)
    _log("Processed at: %s" % date_time_processed)
    _log("Completed at: %s" % date_time_completed)
    _log("Initial delay was: %s" % delay_time)
    _log("Ran for: %s" % run_time)
    _log("Simultation took: %s" % simulation_time)
    _log("Total time taken: %s" % total_time_taken)

    o = open('%s/stdout.txt' % simrun.data_folder, 'a')
    o.write("Simrun timing data:\n")
    o.write("Created at: %s\n" % date_time_created)
    o.write("Started at: %s\n" % date_time_started)
    o.write("Processed at: %s\n" % date_time_processed)
    o.write("Completed at: %s\n" % date_time_completed)
    o.write("Initial delay was: %s\n" % delay_time)
    o.write("Ran for: %s\n" % run_time)
    o.write("Simultation took: %s\n" % simulation_time)
    o.write("Total time taken: %s\n" % total_time_taken)

    o.close()

    gen.set_base_context({'group_name': simrun.group_name, 'instr_displayname': simrun.instr_displayname,
                          'date_time_completed': date_time_completed,
                          'date_time_created': date_time_created,
                          'date_time_started': date_time_started,
                          'date_time_processed': date_time_processed,
                          'total_time_taken': total_time_taken,
                          'delay_time': delay_time,
                          'run_time': run_time,
                          'simulation_time': simulation_time,
                          'params': simrun.params,
                          'neutrons': simrun.neutrons,
                          'seed': simrun.seed,
                          'scanpoints': simrun.scanpoints,
                          'lin_log_html': lin_log_html,
                          'data_folder': simrun.data_folder})

    _log("setting up to generate browsepages")
    _log("datafolder: %s" % simrun.data_folder)
    _log("simrun.plot_files: %s" % simrun.plot_files)
    _log("simrun.data_files: %s" % simrun.data_files)
    if simrun.scanpoints == 1:
        gen.generate_browsepage(simrun.data_folder, simrun.plot_files, simrun.data_files, simrun.skipvisualisation)
    else:
        gen.generate_browsepage_sweep(simrun.data_folder, simrun.plot_files, simrun.data_files, simrun.scanpoints, simrun.skipvisualisation)

def threadwork(simrun, semaphore):
    ''' thread method for simulation and plotting '''
    try:
        # check simrun object age
        check_age(simrun, max_mins=3600)

        # check for existing, similar simruns for reuse
        if simrun.force_run or not cache_check(simrun):

            _log('runremote: %s' % simrun.runremote)

            init_processing(simrun)
            gather_files(simrun)

            if simrun.runremote:
                remote_mcrun(simrun)
            else:
                mcrun(simrun)

            simrun.processed = timezone.now()
            simrun.enable_cachefrom = True

            if simrun.skipvisualisation:
                _log('asked to skip visualisation')
            else:
                mcdisplay_webgl(simrun)
                mcdisplay(simrun)
                mcplot(simrun)

            # post-processing
            maketar(simrun)
            _log('made tar')
            simrun.complete = timezone.now()
            _log('about to write')
            write_results(simrun)
            _log('written results')

        # finish
        simrun.save()

        _log('done (%s secs).' % (simrun.complete - simrun.started).seconds)

    except Exception as e:
        simrun.failed = timezone.now()
        simrun.fail_str = e.__str__()
        simrun.save()

        if e is ExitException:
            raise e

        _log('fail: %s (%s)' % (e.__str__(), type(e).__name__))
        _log_error(e)

    finally:
        _log("releasing semaphore")
        semaphore.release()

def work(threaded=True, semaphore=None):
    ''' iterates non-started SimRun objects, updates statuses, and calls sim, layout display and plot functions '''

    # avoid having two worker threads starting on the same job
    simrun = get_and_start_new_simrun()

    while simrun:
        # exceptions raised during the processing block are written to the simrun object as fail, but do not break the processing loop
        try:
            if simrun.scanpoints == 1:
                _log('delegating simrun for %s...' % simrun.instr_displayname)
            else:
                _log('delegating simrun for %s (%d-point scansweep)...' % (simrun.instr_displayname, simrun.scanpoints))

            if threaded:
                semaphore.acquire() # this will block untill a slot is released
                t = threading.Thread(target=threadwork, args=(simrun, semaphore))
                t.setDaemon(True)
                t.setName('%s (%s)' % (t.getName().replace('Thread-','T'), simrun.instr_displayname))
                t.start()
            else:
                threadwork(simrun)

            # continue or cause a break iteration

        except Exception as e:
            if e is ExitException:
                raise e

            _log('fail: %s (%s)' % (e.__str__(), type(e).__name__))
            _log_error(e)

        finally:
            simrun = get_and_start_new_simrun()
            if not simrun:
                _log("idle...")

_wlog = None
def _log(msg):
    global _wlog
    if not _wlog:
        _wlog = logging.getLogger('worker')
        hdlr = logging.FileHandler('worker.log')
        hdlr.setFormatter(logging.Formatter('%(threadName)-22s: %(message)s', '%Y%m%d_%H%M%S'))

        hdlr2 = logging.StreamHandler(sys.stdout)
        hdlr2.level = logging.INFO
        hdlr2.setFormatter(logging.Formatter('%(threadName)-22s: %(message)s', '%Y%m%d_%H%M%S'))
        _wlog.addHandler(hdlr)
        _wlog.addHandler(hdlr2)

        _wlog.info("")
        _wlog.info("")
        _wlog.info("%%  starting McWeb worker log session  %%")
    _wlog.info(msg)

_elog = None
def _log_error(exception):
    msg = traceback.format_exc()
    global _elog
    if not _elog:
        _elog = logging.getLogger('runworker_unhandled')
        hdlr = logging.FileHandler('runworker_unhandled.log')
        hdlr.level = logging.ERROR
        hdlr.setFormatter(logging.Formatter('%(threadName)-22s: %(message)s', '%Y%m%d_%H%M%S'))

        hdlr2 = logging.StreamHandler(sys.stdout)
        hdlr2.level = logging.ERROR
        hdlr2.setFormatter(logging.Formatter('%(threadName)-22s: %(message)s', '%Y%m%d_%H%M%S'))

        _elog.addHandler(hdlr)
        _elog.addHandler(hdlr2)
    _elog.error(msg)


class Command(BaseCommand):
    ''' django simrun processing command "runworker" '''
    help = 'generates mcstas/mxtrace simulation output and updates db'

    def add_arguments(self, parser):
        ''' adds the debug run option (run only once) '''
        parser.add_argument('--debug', action='store_true', help="runs work() only once")

    def handle(self, *args, **options):
        ''' implements main execution loop and debug run '''
        # enable logging
        logging.basicConfig(level=logging.INFO,
                    format='%(threadName)-22s: %(message)s',
                    )

        # ensure data output dir exists:
        try:
            data_basedir = os.path.join(STATIC_URL.lstrip('/'), DATA_DIRNAME)
            if not os.path.exists(data_basedir):
                os.mkdir(data_basedir)
        except:
            raise ExitException('Could not find or create base data folder, exiting (%s).' % data_basedir)

        # global error handling
        try:
            # debug run
            if options['debug']:
                work(threaded=False)
                exit()

            # main threaded execution loop:
            sema = threading.BoundedSemaphore(MAX_THREADS)
            _log("created semaphore with %d slots" % MAX_THREADS)

            _log("looking for simruns...")
            while True:
                work(threaded=True, semaphore=sema)
                time.sleep(1)

        # ctr-c exits
        except KeyboardInterrupt:
            print("")
            _log("shutdown requested, exiting...")
            print("")
            print("")

        # handle exit-exception (programmatic shutdown)
        except ExitException as e:
            print("")
            _log("exit exception raised, exiting (%s)" % e.__str__())
            print("")
            print("")

        # global exception log to file
        except Exception as e:
            _log_error(e)