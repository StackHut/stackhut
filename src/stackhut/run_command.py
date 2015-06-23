import json
import subprocess
import uuid
import os
import shutil

import barrister
from stackhut.utils import log, BaseCmd, CloudStore, LocalStore
import stackhut.utils as utils

# Module Consts
REQ_FIFO = 'req.json'
RESP_FIFO = 'resp.json'

class RunCmd(BaseCmd):
    """Base Run Command functionality"""
    def __init__(self, args):
        BaseCmd.__init__(self, args)

        # setup the service contracts
        contract = barrister.contract_from_file(utils.CONTRACTFILE)
        self.server = barrister.Server(contract)

        # select the stack
        stack = self.hutfile['stack']
        if stack == 'python':
            self.shim_exe = ['/usr/bin/python3']
            self.shim_file = 'stackrun.py'
        elif stack == 'nodejs':
            self.shim_exe = ['/usr/bin/iojs', '--harmony']
            self.shim_file = 'stackrun.js'
        else:
            log.error("Unknown stack")
            exit(1)
        # copy across the shim file
        shutil.copy(os.path.join(self.shim_dir, self.shim_file), os.getcwd())
        self.shim_cmd = self.shim_exe + [self.shim_file]

    def run(self):
        super().run()

        # called by service on startup
        def _startup():
            log.debug('Starting up service')

            try:
                input_json = json.loads(self.get_request())
            except:
                raise utils.ParseError()
            log.info('Input - \n{}'.format(input_json))

            # massage the JSON-RPC request if we don't receieve an entirely valid req
            default_service = input_json['serviceName']

            def _make_json_rpc(req):
                req['jsonrpc'] = "2.0" if 'jsonrpc' not in req else req['jsonrpc']
                req['id'] = str(uuid.uuid4()) if 'id' not in req else req['id']
                # add the default interface if none exists
                if req['method'].find('.') < 0:
                    req['method'] = "{}.{}".format(default_service, req['method'])
                return req

            if 'req' in input_json:
                reqs = input_json['req']
                if type(reqs) is list:
                    reqs = [_make_json_rpc(req) for req in reqs]
                else:
                    reqs = _make_json_rpc(reqs)
            else:
                raise utils.ParseError()

            os.mkfifo(REQ_FIFO)
            os.mkfifo(RESP_FIFO)

            return reqs  # anything else

        # called by service on exit - clean the system, write all output data and return control back to docker
        # intended to upload all files into S#
        def _shutdown(res):
            log.info('Output - \n{}'.format(res))
            log.info('Shutting down service')
            # cleanup
            os.remove(REQ_FIFO)
            os.remove(RESP_FIFO)
            # save output and log
            self.put_response(json.dumps(res))
            self.put_file(utils.LOGFILE)

        def _run_ext(method, params):
            """Make a pseudo-function call across languages"""
            # TODO - optimise
            # write the req
            req = dict(method=method, params=params)

            # call out to sub process
            p = subprocess.Popen(self.shim_cmd, shell=False, stderr=subprocess.STDOUT)
            # blocking-wait to send the request
            with open(REQ_FIFO, "w") as f:
                f.write(json.dumps(req))
            # blocking-wait to read the resp
            with open(RESP_FIFO, "r") as f:
                resp = json.loads(f.read())

            # now wait for completion
            # TODO - is this needed?
            p.wait()
            if p.returncode != 0:
                raise utils.NonZeroExitError(p.returncode, p.stdout)

            # basic error handling
            if 'error' in resp:
                code = resp['error']
                if code == barrister.ERR_METHOD_NOT_FOUND:
                    raise utils.ServerError(code, "Method or service {} not found".format(method))
                else:
                    raise utils.ServerError(code, resp['msg'])
            # return if no issue
            return resp['result']

        # Now run the main rpc commands
        try:
            req = _startup()
            resp = self.server.call(req, dict(callback=_run_ext))
            _shutdown(resp)
        except Exception as e:
            log.exception("Shit, unhandled error! - {}".format(e))
            exit(1)
        finally:
            os.remove(os.path.join(os.getcwd(), self.shim_file))

        # quit with correct exit code
        log.info('Service call complete')
        return 0


class RunLocalCmd(RunCmd, utils.LocalStore):
    """"Concrete Run Command using local files for dev"""

    def __init__(self, args):
        utils.LocalStore.__init__(self, args.infile)
        RunCmd.__init__(self, args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunLocalCmd, RunLocalCmd).parse_cmds(subparser,
                                                               'runlocal', "Run a StackHut service locally", RunLocalCmd)
        subparser.add_argument("--infile", '-i', default='demo_input.json',
                               help="Local file to use for input")

class RunCloudCmd(RunCmd, utils.CloudStore):
    """Concrete Run Command using Cloud systems for prod"""

    def __init__(self, args):
        super(RunCmd, self).__init__(args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunCloudCmd, RunCloudCmd).parse_cmds(subparser, 'run', "Run a StackHut service", RunCloudCmd)
        subparser.add_argument("task_id", help="Id representing the specific task")
        subparser.add_argument("aws_id", help="Key used to communicate with AWS")
        subparser.add_argument("aws_key", help="Key used to communicate with AWS")
