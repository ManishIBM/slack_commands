import subprocess
import sys

SUBPROCESS_TIMEOUT = 60


class SubprocessExecution():
    """
    Purpose: Class to perform shell command execution using subprocess
    """

    def __init__(self, log):
        self.log = log
        self.std_error = ''

    def exec_process(self, cmd, timeout=SUBPROCESS_TIMEOUT,
                     expected_return_code=0, print_stdout=True):
        """"
        Objective: Execute the oc command using subprocess

        @param cmd: List of strings
        @param timeout: process will wait for SUBPROCESS_TIMEOUT, if
            execution is still in progress(test suite execution
            blocked), raises TimeoutExpired exception and
            Catching this exception and retrying communication
            will not lose any output.
        @param expected_return_code: expected returned code. In some cases
        return code is non-zero and expected output is present in stdout.
        Specially the case where the command is depricated

        @return command output in 'utf-8' format upon success
                None upon cmd execution failure
                :param return_code:
        """
        self.log.info("Executing in {} ".format(sys._getframe(
            1).f_code.co_name))
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout = None
            stderr = None

            stdout, stderr = process.communicate(timeout=timeout)
            return_code = process.returncode

            if stderr:
                self.std_error = stderr.decode('utf-8')
                self.log.info('stdout %s', stdout)
            if stderr and not return_code and not stdout:
                raise subprocess.CalledProcessError(return_code, cmd, stderr)
            if return_code != expected_return_code:
                self.log.info('returned code: {}, expected return code: {}'
                              ''.format(return_code, expected_return_code))
                raise Exception(
                    "{} failed with error {} and the output is {}".format(
                        cmd[0] + cmd[1], stderr, stdout))
            if print_stdout:
                self.log.info("Command executed: {} Result of the command: "
                              "{}".format(cmd, stdout.decode("utf-8")))
            return stdout.decode("utf-8")
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self.log.info("{} execution timedout with stdout {} and stderr {}"
                          "".format(cmd, stdout, stderr))
        except subprocess.CalledProcessError as e:
            self.log.error("{} execution failed with STDERR {} and Exception "
                           "{} ".format(cmd, stderr, str(e)))
        except Exception as e:
            self.log.error("{} exception raised while executing command {} "
                           "".format(str(e), cmd))
        return None

    def nested_exec_process(self, cmd, input_cmd, timeout=SUBPROCESS_TIMEOUT,
                            expected_return_code=0):
        """"
        Objective: Execute the oc command using subprocess and nestetd cmds
        execution.

        @param cmd: List of strings / parent command to be executed
        @param input_cmd: list of nested commands to be executed
                          post parent command.
        @param timeout: process will wait for SUBPROCESS_TIMEOUT, if
            execution is still in progress(test suite execution
            blocked), raises TimeoutExpired exception and
            Catching this exception and retrying communication
            will not lose any output.
        @param expected_return_code: expected returned code. In some cases
        return code is non-zero and expected output is present in stdout.
        Specially the case where the command is depricated.

        @return command output in 'utf-8' format upon success
                None upon cmd execution failure
        for example : to execute the oc debug command and list of nested cmds
         in debug shell.
         cmd1 = "oc debug node/compute-0.isf-rackh.rtp.raleigh.ibm.com"
         nested command :
         cmd2 = "chroot /host"
         cmd3 = "grep pids_limit /etc/crio/crio.conf | cut -d\"=\" -f2-"

         cmd1 = shlex.split('oc debug node/' + hostname)
        input_cmd = ['chroot /host', 'grep  pids_limit /etc/crio/crio.conf
        | cut -d"=" -f2-']
        self.nested_exec_process(
                cmd, input_cmd, expected_return_code=return_code)
        """
        self.log.info("Executing in {} ".format(sys._getframe(
            1).f_code.co_name))
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout = None
            stderr = None
            if input_cmd is not None:
                input_cmd = bytes("\n".join(input_cmd)+'\n', 'utf-8')
            stdout, stderr = process.communicate(input=input_cmd,
                                                 timeout=timeout)
            return_code = process.returncode
            if return_code != expected_return_code:
                self.log.info('returned code: {}, expected return code: {}'
                              ''.format(return_code, expected_return_code))
                raise Exception(
                    "{} failed with error {} and the output is {}".format(
                        cmd[0] + cmd[1], stderr, stdout))
            self.log.info("Command executed: {} Result of the command: "
                          "{}".format(cmd, stdout.decode("utf-8")))
            return stdout.decode("utf-8")
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self.log.info("{} execution timedout with stdout {} and stderr {}"
                          "".format(cmd, stdout, stderr))
        except Exception as e:
            self.log.error("{} exception raised while executing command {} "
                           "".format(str(e), cmd))
        return None

    def get_stderror_op(self):
        return self.std_error
