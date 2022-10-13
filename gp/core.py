import sys
import urllib
import base64
import json
import time
from contextlib import closing
import urllib.request
import urllib.parse
import urllib.error


GP_JOB_TAG = 'GenePattern Python Client'


class GPServer(object):
    """
    Wrapper for data needed to make server calls.

    Wraps the server url, username and password, and provides helper function
    to construct the authorization header.
    """

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.token = None
        self.last_job = None

    def __str__(self):
        return self.url + ' ' + self.username

    def authorization_header(self):
        """
        Returns a string containing the authorization header used to authenticate
        with GenePattern. This string is included in the header of subsequent
        requests sent to GenePattern.
        """
        return 'Basic %s' % base64.b64encode(bytes(self.username + ':' + self.password, 'ascii')).decode('ascii')
    
    def system_message(self):
        url = f"{self.url}/rest/v1/config/system-message"
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        return response.read().decode('utf-8')
    
    def login(self):
        """Log in to the OAuth2 endpoint"""
        safe_username = urllib.parse.quote(self.username)
        safe_password = urllib.parse.quote(self.password)
        url = f"{self.url}/rest/v1/oauth2/token?grant_type=password&username={safe_username}&password={safe_password}&client_id=GenePatternNotebook-{safe_username}"

        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request, b'')
        if response.getcode() != 200:
            raise urllib.error.HTTPError(url, response.getcode(), 'Invalid username or password', response.getheaders(), None)
        self.token = json.loads(response.read())['access_token']
        return self.token

    def upload_file(self, file_name, file_path):
        """
        Upload a file to a server

        Attempts to upload a local file with path filepath, to the server, where it
        will be named filename.

        Args:
            :param file_name: The name that the uploaded file will be called on the server.
            :param file_path: The path of the local file to upload.

        Returns:
            :return: A GPFile object that wraps the URI of the uploaded file, or None if the upload fails.
        """

        request = urllib.request.Request(self.url + '/rest/v1/data/upload/job_input?name=' + urllib.parse.quote(file_name))
        if self.authorization_header() is not None:
            request.add_header('Authorization', self.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        with open(file_path, 'rb') as f:
            data = f.read()

        try:
            response = urllib.request.urlopen(request, data)
        except IOError:
            print("authentication failed")
            return None

        if response.getcode() != 201:
            print("file upload failed, status code = %i" % response.getcode())
            return None

        return GPFile(self, response.info().get('Location'))

    def run_job(self, job_spec, wait_until_done=True):
        """
        Runs a job defined by jobspec, optionally non-blocking.

        Takes a GPJobSpec object that defines a request to run a job, and makes the
        request to the server.  By default blocks until the job is finished by
        polling the server, but can also run asynchronously.

        Args:
            :param job_spec: A GPJobSpec object that contains the data defining the job to be run.
            :param wait_until_done: Whether to wait until the job is finished before returning.
            :return:

        Returns:
            a GPJob object that refers to the running job on the server.  If called
            synchronously, this object will contain the info associated with the
            completed job.  Otherwise, it will just wrap the URI of the running job.
        """

        # names should be a list of names,
        # values should be a list of **lists** of values
        json_string = json.dumps({'lsid': job_spec.lsid, 'params': job_spec.params, 'tags': [GP_JOB_TAG]}, cls=GPJSONEncoder)
        if sys.version_info.major == 3:  # Handle conversion to bytes for Python 3
            json_string = bytes(json_string, 'utf-8')
        request = urllib.request.Request(self.url + '/rest/v1/jobs')
        if self.authorization_header() is not None:
            request.add_header('Authorization', self.authorization_header())
        request.add_header('Content-Type', 'application/json')
        request.add_header('User-Agent', 'GenePatternRest')
        response = urllib.request.urlopen(request, json_string)
        if response.getcode() != 201:
            print(" job POST failed, status code = %i" % response.getcode())
            return None
        data = json.loads(response.read().decode('utf-8'))
        job = GPJob(self, data['jobId'])
        job.get_info()
        self.last_job = job  # Set the last job
        if wait_until_done:
            job.wait_until_done()
        return job

    def get_token(self):
        """Return the authentication token, logging in to obtain it if necessary"""
        if self.token: return self.token
        else: return self.login()

    def get_job(self, job_number):
        job = GPJob(self, job_number)
        return job

    def get_task_list(self):
        """
        Queries the GenePattern server and returns a list of GPTask objects,
        each representing one of the modules installed on the server. Useful
        for determining which are available on the server.
        """
        request = urllib.request.Request(self.url + '/rest/v1/tasks/all.json')
        if self.authorization_header() is not None:
            request.add_header('Authorization', self.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        response = urllib.request.urlopen(request)
        response_string = response.read().decode('utf-8')
        category_and_tasks = json.loads(response_string)
        raw_list = category_and_tasks['all_modules']
        task_list = []
        for task_dict in raw_list:
            task = GPTask(self, task_dict['lsid'], task_dict)
            task_list.append(task)
        return task_list

    @staticmethod
    def wait_until_complete(job_list):
        """
        Args: Accepts a list of GPJob objects

        This method will not return until all GPJob objects in the list have
        finished running. That us, they are either complete and have resulted in
        an error state.

        This method will occasionally query each job to see if it is finished.
        """
        complete = [False] * len(job_list)
        wait = 1
        while not all(complete):
            time.sleep(wait)
            for i, job in enumerate(job_list):
                if not complete[i]:
                    complete[i] = job.is_finished()
                    if not complete[i]:
                        break
            wait = min(wait * 2, 10)

    def get_recent_jobs(self, n_jobs=10):
        """
        Returns the user's N most recently submitted jobs on the GenePattern server.

        Args: If not specified, n_jobs = 10.

        Returns: An array of GPJob objects.
        """

        # Query the server for the list of jobs
        request = urllib.request.Request(self.url + '/rest/v1/jobs/?pageSize=' +
                                         str(n_jobs) + '&userId=' + str(urllib.parse.quote(self.username)) +
                                         '&orderBy=-dateSubmitted')
        if self.authorization_header() is not None:
            request.add_header('Authorization', self.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        response = urllib.request.urlopen(request)
        response_string = response.read().decode('utf-8')
        response_json = json.loads(response_string)

        # For each job in the JSON Array, build a GPJob object and add to the job list
        job_list = []
        for job_json in response_json['items']:
            job_id = job_json['jobId']
            job = GPJob(self, job_id)
            job.info = job_json
            job.load_info()
            job_list.append(job)

        return job_list


class GPResource(object):
    """
    Base class for resources on a Gene Pattern server.

    Wraps references to resources on a Gene Pattern server, which are all
    defined by a URI.  Subclasses can implement custom logic appropriate for
    that resources such as downloading a file or info for a running or completed
    job.
    """
    uri = None

    def __init__(self, uri):
        self.uri = uri


class GPFile(GPResource):
    """
    A file on a Gene Pattern server.

    Wraps the URI of the file, and contains methods to download the file.
    """
    server_data = None

    def __init__(self, server_data, uri):
        GPResource.__init__(self, uri)
        self.server_data = server_data

    def open(self):
        """
        Opens the URL associated with the GPFile and returns a file-like object
        with three extra methods:

            * geturl() - return the ultimate URL (can be used to determine if a
                redirect was followed)

            * info() - return the meta-information of the page, such as headers

            * getcode() - return the HTTP status code of the response
        """
        request = urllib.request.Request(self.uri)
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        try:
            return urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            if e.geturl():  # Handle S3 redirects if one is encountered
                return urllib.request.urlopen(urllib.request.Request(e.geturl()))
            else:
                raise e

    def read(self):
        """
        Reads the contents of the GPFile and returns the contents as a string (assumes UTF-8)
        """
        with closing(self.open()) as f:
            data = f.read()
        return data.decode("utf-8") or None

    def get_url(self):
        """
        Returns the URL to the GPFile
        """
        return self.uri

    def get_name(self):
        """
        Returns the file name of the output file
        """
        return urllib.parse.unquote(self.get_url().split('/')[-1])

    def __str__(self):
        return self.uri


class GPJob(GPResource):
    """
    A running or completed job on a Gene Pattern server.

    Contains methods to get the info of the job, and to wait on a running job by
    polling the server until the job is completed.
    """
    json = None  # Define the backing JSON string
    info = None
    server_data = None
    task_name = None
    task_lsid = None
    user_id = None
    job_number = None
    status = None
    date_submitted = None
    log_files = None
    output_files = None
    num_output_files = None
    children = None
    input_params = None

    def __init__(self, server_data, uri):
        super(GPJob, self).__init__(str(uri))
        self.info = None
        self.server_data = server_data
        self.job_number = uri

    def get_info(self):
        """
        Query the GenePattern server for metadata regarding this job and assign
        that metadata to the properties on this GPJob object. Including:
            * Task Name
            * LSID
            * User ID
            * Job Number
            * Status
            * Date Submitted
            * URL of Log Files
            * URL of Output Files
            * Number of Output Files
        """
        request = urllib.request.Request(self.server_data.url + "/rest/v1/jobs/" + self.uri + "?includeInputParams=true")
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        response = urllib.request.urlopen(request)

        self.json = response.read().decode('utf-8')
        self.info = json.loads(self.json)
        self.load_info()

    def load_info(self):
        """
        Parses the JSON object stored at GPJob.info and assigns its metadata to
        properties of this GPJob object.

        Primarily intended to be called from GPJob.get_info().
        """
        self.task_name = self.info['taskName']
        self.task_lsid = self.info['taskLsid']
        self.user_id = self.info['userId']
        self.job_number = int(self.info['jobId'])
        self.status = self.get_status_message()
        self.date_submitted = self.info['dateSubmitted']
        self.log_files = self.info['logFiles']
        self.output_files = self.info['outputFiles']
        self.num_output_files = self.info['numOutputFiles']
        self.input_params = self.info['inputParams']

        # Create children, if relevant
        self.children = self.get_child_jobs()

    def get_input_params(self):
        """Return the input parameters used to launch the job"""

        # Lazily load info
        if self.info is None: self.get_info()

        return { list(p.keys())[0]:list(p.values())[0] for p in self.input_params }

    def get_child_jobs(self):
        """
        Queries the GenePattern server for child jobs of this job, creates GPJob
        objects representing each of them and assigns the list of them to the
        GPJob.children property. Then return this list.
        """
        # Lazily load info
        if self.info is None:
            self.get_info()

        # Lazily load children
        if self.children:
            return self.children
        else:
            if 'children' in self.info:
                child_list = []
                for child in self.info['children']['items']:
                    child_job = GPJob(self.server_data, child['jobId'])
                    child_job.info = child
                    child_job.load_info()
                    child_list.append(child_job)
                return child_list
            else:               # No children? Return empty list
                return []

    def is_finished(self):
        """
        Queries the server to check if the job has been completed.
        Returns True or False.
        """
        self.get_info()

        if 'status' not in self.info:
            return False
        if 'isFinished' not in self.info['status']:
            return False

        return self.info['status']['isFinished']

    def has_error(self):
        """
        Queries the server to check if the job has an error.
        Returns True or False.
        """
        self.get_info()

        if 'status' not in self.info:
            return False
        if 'hasError' not in self.info['status']:
            return False

        return self.info['status']['hasError']

    def is_pending(self):
        """
        Queries the server to check if the job is pending.
        Returns True or False.
        """
        self.get_info()

        if 'status' not in self.info:
            return False
        if 'isPending' not in self.info['status']:
            return False

        return self.info['status']['isPending']

    def get_status_message(self):
        """
        Returns the status message for the job, querying the
        server if necessary.
        """
        # Lazily load info
        if self.info is None:
            self.get_info()

        return self.info['status']['statusMessage']

    def get_tags(self):
        """
        Returns the tags for the job, querying the
        server if necessary.
        """
        # Lazily load info
        if self.info is None:
            self.get_info()

        if 'tags' in self.info:
            return [structure['tag']['tag'] for structure in self.info['tags']]
        else:
            return []

    def get_comments(self):
        """
        Returns the comments for the job, querying the
        server if necessary.
        """
        # Lazily load info
        if self.info is None:
            self.get_info()

        if 'comments' in self.info:
            return [structure['text'] for structure in self.info['comments']['comments']]
        else:
            return []

    def get_output_files(self):
        """
        Returns a list of the files output by the job, querying the server if
        necessary. If the job has output no files, an empty list will be
        returned.
        """
        # Lazily load info
        if self.info is None:
            self.get_info()

        if 'outputFiles' in self.info:
            return [GPFile(self.server_data, f['link']['href']) for f in self.info['outputFiles']]
        else:
            return []

    def get_file(self, name):
        """
        Returns the output file with the specified name, if no output files
        match, returns None.
        """
        files = self.get_output_files()
        for f in files:
            if f.get_name() == name:
                return f
        return None

    def wait_until_done(self):
        """
        This method will not return until the job is either complete or has
        reached an error state. This queries the server periodically to check
        for an update in status.
        """
        wait = 1
        while True:
            time.sleep(wait)
            self.get_info()
            if self.info['status']['isFinished']:
                break
            # implements a crude exponential back off
            wait = min(wait * 2, 60)

    def get_job_status_url(self):
        """
        Returns the URL of the job's status page on the GenePattern server
        """
        return self.server_data.url + "/pages/index.jsf?jobid=" + self.uri
    
    def get_permissions(self):
        """Get the permissions object for the GP job"""
        url = f'{self.server_data.url}/rest/v1/jobs/{self.job_number}/permissions'
        request = urllib.request.Request(url)
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')

        response = urllib.request.urlopen(request)
        return json.loads(response.read())
        
    def set_permissions(self, permissions):
        """Set the group permissions for the job"""
        url = f'{self.server_data.url}/rest/v1/jobs/{self.job_number}/permissions'
        data = json.dumps(permissions).encode('utf8')
        request = urllib.request.Request(url, data=data, method='PUT')
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        urllib.request.urlopen(request)

    def terminate(self):
        """Terminate a running or pending job"""
        url = f'{self.server_data.url}/rest/v1/jobs/{self.job_number}/terminate'
        request = urllib.request.Request(url, method='DELETE')
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        return urllib.request.urlopen(request).code == 200


class GPJobSpec(object):
    """
    Data needed to make a request to perform a job on a Gene Pattern server

    Encapsulates the data needed to make a server call to run a job.  This
    includes the LSID of the job, and the parameters.  Helper methods set
    the LSID and parameters.
    """

    def __init__(self, server_data, lsid):
        self.params = []
        self.lsid = lsid
        self.server_data = server_data

    def set_parameter(self, name, values, group_id=None):
        """
        Sets the value of a parameter for the GPJobSpec
        :param name: name of the parameter
        :param values: list of values for the parameter
        :param group_id: optional parameter group ID
        :return:
        """
        if not isinstance(values, list):
            values = [values]
        if group_id is None:
            self.params.append({'name': name, 'values': values})
        else:
            self.params.append({'name': name, 'groupId': group_id, 'values': values})


class GPTask(GPResource):
    """Describes a GenePattern task (module or pipeline).

    The constructor retrieves data transfer object (DTO) describing task from GenePattern server.
    The DTO contains general task information (LSID, Category, Description, Version comment),
    a parameter list and a list of initial values.  Class includes getters for each of these
    components.

    """
    json = None  # Define the backing JSON string
    server_data = None
    description = None
    name = None
    documentation = None
    lsid = None
    version = None
    params = None
    dto = None

    _params_loaded = False
    submit_json = None
    job_spec = None
    job = None
    job_number = None

    def __init__(self, server_data, name_or_lsid, task_dict=None):
        GPResource.__init__(self, name_or_lsid)
        self.server_data = server_data

        # Initialize descriptive attributes if available
        if task_dict is not None:
            if 'name' in task_dict:
                self.name = task_dict['name']
            if 'lsid' in task_dict:
                self.lsid = task_dict['lsid']
            if 'description' in task_dict:
                self.description = task_dict['description']
            if 'documentation' in task_dict:
                self.documentation = task_dict['documentation']
            if 'version' in task_dict:
                self.version = task_dict['version']

    def param_load(self):
        """
        Queries the server for the parameter information and other metadata associated with
        this task
        """
        escaped_uri = urllib.parse.quote(self.uri)
        request = urllib.request.Request(self.server_data.url + '/rest/v1/tasks/' + escaped_uri)
        if self.server_data.authorization_header() is not None:
            request.add_header('Authorization', self.server_data.authorization_header())
        request.add_header('User-Agent', 'GenePatternRest')
        response = urllib.request.urlopen(request)
        self.json = response.read().decode('utf-8')
        self.dto = json.loads(self.json)

        self.description = self.dto['description'] if 'description' in self.dto else ""
        self.name = self.dto['name']
        self.documentation = self.dto['documentation'] if 'documentation' in self.dto else ""
        self.lsid = self.dto['lsid']
        self.version = self.dto['version'] if 'version' in self.dto else ""
        self.params = []
        for param in self.dto['params']:
            self.params.append(GPTaskParam(self, param))
        self._params_loaded = True

    def get_lsid(self):
        """
        :return: Returns the task's LSID as a string
        """
        return self.lsid

    def get_name(self):
        """
        :return: Returns the task's name as a string
        """
        return self.name

    def get_description(self):
        """
        :return: Returns the task's description as a string
        """
        return self.description

    def get_version(self):
        """
        :return: Returns the task's version as a string
        """
        return self.version

    def get_parameters(self):
        """
        :return: Returns a list of GPTaskParam objects representing the parameters for this
        task, in order
        """
        return self.params

    def make_job_spec(self):
        """
        :return: Returns a GPJobSpec used to launch a job of this task type
        """
        # If the parameters haven't been loaded yet, do so
        if not self._params_loaded and self.server_data is not None:
            self.param_load()

        return GPJobSpec(self.server_data, self.lsid)


class GPTaskParam(object):
    """
    Encapsulates single parameter information.

    The constructor's input parameter is the data transfer object
    associated with a single task parameter (i.e., element from list
    returned by GPTask.getParameters)
    """
    task = None
    dto = None
    name = None
    description = None
    attributes = None

    def __init__(self, task, dto):
        self.task = task
        self.dto = dto
        self.name = list(dto)[0]
        if 'description' in dto[self.name]:
            self.description = dto[self.name]['description']
        else:
            self.description = ''
        self.attributes = dto[self.name]['attributes']

    def get_dto(self):
        """
        Returns a raw object representing the parameter. This is mostly used to
        initialize GPTaskParam objects
        """
        return self.dto

    def get_name(self):
        """
        :return: Returns the parameter name as a string
        """
        return self.name

    def is_optional(self):
        """
        Returns whether the parameter is optional or required
        :return: Return True if optional, False if required
        """
        if (('optional' in self.attributes and bool(self.attributes['optional'].strip())) or
                ('minValue' in self.attributes and self.attributes['minValue'] == 0)):
            return True
        else:
            return False

    def get_description(self):
        """
        :return: Returns the parameter description as a string
        """
        return self.description

    def get_type(self):
        """
        Returns either 'File' or 'String'.

        The type attribute (e.g., java.io.File, java.lang.Integer, java.lang.Float),
        which might give a hint as to what string should represent,
        is not enforced and not employed consistently across all tasks, so we ignore.
        """

        if 'TYPE' in self.attributes and 'MODE' in self.attributes:
            dto_type = self.attributes['TYPE']
            dto_mode = self.attributes['MODE']
            if dto_type == 'FILE' and dto_mode == 'IN':
                return 'File'
        return 'String'

    def is_password(self):
        """
        Indicates whether password flag associated with string parameter.

        If string parameter flagged as password, UI should not display
        parameter value on input field (e.g., mask out with asterisks).

        """

        if 'type' in self.attributes and self.attributes['type'] == 'PASSWORD':
            return True
        else:
            return False

    def allow_multiple(self):
        """
        Return whether the parameter allows multiple values or not
        :return: Return True if the parameter allows multiple values, otherwise False
        """
        # note that maxValue means "max number of values", and is an integer, not a string
        if ('maxValue' in self.attributes) and (self.attributes['maxValue'] > 1):
            return True
        elif ('numValues' in self.attributes) and ('+' in self.attributes['numValues']):
            return True
        else:
            return False

    def get_default_value(self):
        """
        Return the default value for the parameter. If here is no default value, return None
        """
        if ('default_value' in self.attributes and
                bool(self.attributes['default_value'].strip())):
            return self.attributes['default_value']
        else:
            return None

    def is_choice_param(self):
        """
        :return: Return True if this is a choice parameter, otherwise False
        """
        return 'choiceInfo' in self.dto[self.name]

    def get_choice_status(self):
        """
        Returns a message field, which indicates whether choices statically
        or dynamically defined, and flag indicating whether a dynamic file
        selection loading error occurred.

        Throws an error if this is not a choice parameter.
        """
        if 'choiceInfo' not in self.dto[self.name]:
            raise GPException('not a choice parameter')

        status = self.dto[self.name]['choiceInfo']['status']
        return status['message'], status['flag']

    def get_choice_href(self):
        """
        Returns the HREF of a dynamic choice parameter.
        Throws an error if this is not a choice parameter.
        """
        if 'choiceInfo' not in self.dto[self.name]:
            raise GPException('not a choice parameter')

        return self.dto[self.name]['choiceInfo']['href']

    def get_choice_selected_value(self):
        """
        Returns the default selection from a choice menu
        Throws an error if this is not a choice parameter.
        """
        if 'choiceInfo' not in self.dto[self.name]:
            raise GPException('not a choice parameter')
        choice_info_dto = self.dto[self.name]['choiceInfo']
        if 'selectedValue' in choice_info_dto:
            return self.dto[self.name]['choiceInfo']['selectedValue']
        else:
            return None

    def allow_choice_custom_value(self):
        """
        Returns boolean indicating whether choice parameter supports custom value.

        If choice parameter supports custom value, user can provide parameter value
        other than those provided in choice list.
        """
        if 'choiceInfo' not in self.dto[self.name]:
            raise GPException('not a choice parameter')
        return self._is_string_true(self.dto[self.name]['choiceInfo']['choiceAllowCustom'])

    # this needs additional work - some kind of limited polling to give server time to assemble list
    def get_choices(self):
        """
        Returns a list of dictionary objects, one dictionary object per choice.

        Each object has two keys defined: 'value', 'label'.
        The 'label' entry is what should be displayed on the UI, the 'value' entry
        is what is written into GPJobSpec.
        """

        if 'choiceInfo' not in self.dto[self.name]:
            raise GPException('not a choice parameter')
        if self.get_choice_status()[1] == "NOT_INITIALIZED":
            print(self.get_choice_status())
            print("choice status not initialized")

            request = urllib.request.Request(self.get_choice_href())
            if self.task.server_data.authorization_header() is not None:
                request.add_header('Authorization', self.task.server_data.authorization_header())
            request.add_header('User-Agent', 'GenePatternRest')
            response = urllib.request.urlopen(request)
            self.dto[self.name]['choiceInfo'] = json.loads(response.read().decode('utf-8'))
        return self.dto[self.name]['choiceInfo']['choices']

    def get_alt_name(self):
        """
        Returns the alternate name of a parameter.
        Only pipeline prompt-when-run parameters
        can have alternate names and alternate descriptions
        """
        if ('altName' in self.attributes and
                bool(self.attributes['altName'].strip())):
            return self.attributes['altName']
        else:
            return None

    def get_alt_description(self):
        """
        Returns the alternate description of a parameter.
        Only pipeline prompt-when-run parameters
        can have alternate names and alternate descriptions
        """
        if 'altDescription' in self.attributes and bool(self.attributes['altDescription'].strip()):
            return self.attributes['altDescription']
        else:
            return None

    @staticmethod
    def _is_string_true(test):
        """
        Determines whether a string value is "True" for the purposes of GenePattern's
        parameter parsing
        """
        if type(test) is bool:
            return test
        return test.lower() in ('on', 'yes', 'true')


class GPException(Exception):
    """
    An exception raised by GenePattern and returned to the user
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class GPJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for encoding GenePattern classes
    """
    def default(self, o):
        if isinstance(o, GPFile):
            return o.get_url()

        return {'__{}__'.format(o.__class__.__name__): o.__dict__}
